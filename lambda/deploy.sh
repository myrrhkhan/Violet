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
