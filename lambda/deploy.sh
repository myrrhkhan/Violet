#!/usr/bin/env bash
set -euo pipefail

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI not found. Install and authenticate AWS CLI first."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found. Install Docker and start the daemon first."
  exit 1
fi

if [[ -z "${FUNCTION_NAME:-}" ]]; then
  echo "FUNCTION_NAME is required."
  echo "Example: FUNCTION_NAME=violet-ocr AWS_REGION=us-east-1 ./lambda/deploy.sh"
  exit 1
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
ECR_REPO_NAME="${ECR_REPO_NAME:-${FUNCTION_NAME}}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}"
SMOKE_TEST_LOCAL="${SMOKE_TEST_LOCAL:-0}"
LOCAL_TEST_IMAGE="${LOCAL_TEST_IMAGE:-./client/testimg.jpg}"

echo "Using:"
echo "  FUNCTION_NAME=${FUNCTION_NAME}"
echo "  AWS_REGION=${AWS_REGION}"
echo "  AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}"
echo "  ECR_REPO_NAME=${ECR_REPO_NAME}"
echo "  IMAGE_URI=${IMAGE_URI}"

echo "Ensuring ECR repository exists..."
if ! aws ecr describe-repositories --region "${AWS_REGION}" --repository-names "${ECR_REPO_NAME}" >/dev/null 2>&1; then
  aws ecr create-repository \
    --region "${AWS_REGION}" \
    --repository-name "${ECR_REPO_NAME}" \
    --image-scanning-configuration scanOnPush=true \
    >/dev/null
fi

echo "Logging Docker in to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building image from lambda/Dockerfile..."
docker build --platform linux/amd64 -t "${IMAGE_URI}" "./lambda"

if [[ "${SMOKE_TEST_LOCAL}" == "1" ]]; then
  if [[ ! -f "${LOCAL_TEST_IMAGE}" ]]; then
    echo "SMOKE_TEST_LOCAL=1 but image file not found: ${LOCAL_TEST_IMAGE}"
    exit 1
  fi

  echo "Running local smoke test before push..."
  SMOKE_CONTAINER_NAME="violet-ocr-smoke"
  docker rm -f "${SMOKE_CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker run --rm -d --name "${SMOKE_CONTAINER_NAME}" -p 9000:8080 "${IMAGE_URI}" >/dev/null
  cleanup_smoke() {
    docker rm -f "${SMOKE_CONTAINER_NAME}" >/dev/null 2>&1 || true
  }
  trap cleanup_smoke EXIT

  for _ in $(seq 1 60); do
    if curl -sS "http://127.0.0.1:9000/2015-03-31/functions/function/invocations" -d '{}' >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  python3 -c 'import base64, json, pathlib; p=pathlib.Path("'"${LOCAL_TEST_IMAGE}"'"); print(json.dumps({"httpMethod":"POST","isBase64Encoded":True,"body":base64.b64encode(p.read_bytes()).decode()}))' > /tmp/violet-smoke-payload.json
  SMOKE_RESPONSE="$(curl -sS -X POST "http://127.0.0.1:9000/2015-03-31/functions/function/invocations" -H "Content-Type: application/json" -d @/tmp/violet-smoke-payload.json)"
  SMOKE_STATUS="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("statusCode",""))' "${SMOKE_RESPONSE}")"
  if [[ "${SMOKE_STATUS}" != "200" ]]; then
    echo "Local smoke test failed: ${SMOKE_RESPONSE}"
    exit 1
  fi

  cleanup_smoke
  trap - EXIT
  echo "Local smoke test passed."
fi

echo "Pushing image to ECR..."
docker push "${IMAGE_URI}"

echo "Checking if Lambda exists..."
if aws lambda get-function --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}" >/dev/null 2>&1; then
  echo "Updating Lambda code to new image..."
  aws lambda update-function-code \
    --region "${AWS_REGION}" \
    --function-name "${FUNCTION_NAME}" \
    --image-uri "${IMAGE_URI}" \
    >/dev/null
else
  if [[ -z "${LAMBDA_ROLE_ARN:-}" ]]; then
    echo "Lambda function not found."
    echo "Set LAMBDA_ROLE_ARN to create it:"
    echo "FUNCTION_NAME=${FUNCTION_NAME} AWS_REGION=${AWS_REGION} LAMBDA_ROLE_ARN=arn:aws:iam::<account-id>:role/<role-name> ./lambda/deploy.sh"
    exit 1
  fi

  echo "Creating Lambda from container image..."
  aws lambda create-function \
    --region "${AWS_REGION}" \
    --function-name "${FUNCTION_NAME}" \
    --package-type Image \
    --code ImageUri="${IMAGE_URI}" \
    --role "${LAMBDA_ROLE_ARN}" \
    --timeout "${LAMBDA_TIMEOUT:-30}" \
    --memory-size "${LAMBDA_MEMORY_MB:-1024}" \
    --architectures "${LAMBDA_ARCH:-x86_64}" \
    >/dev/null
fi

echo "Waiting for Lambda update to finish..."
aws lambda wait function-updated --region "${AWS_REGION}" --function-name "${FUNCTION_NAME}"

echo "Done. Current Lambda image:"
aws lambda get-function \
  --region "${AWS_REGION}" \
  --function-name "${FUNCTION_NAME}" \
  --query 'Code.ImageUri' \
  --output text
