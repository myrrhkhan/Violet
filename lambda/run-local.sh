#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${LOCAL_IMAGE_NAME:-violet-ocr-local}"
RIE_PORT="${LOCAL_RIE_PORT:-9000}"
PROXY_PORT="${LOCAL_PROXY_PORT:-3001}"
CONTAINER_NAME="${LOCAL_CONTAINER_NAME:-violet-ocr-local}"

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "Building local lambda image: ${IMAGE_NAME}"
docker build --platform linux/amd64 -t "${IMAGE_NAME}" "./lambda"

echo "Starting lambda container on localhost:${RIE_PORT}"
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run --rm --name "${CONTAINER_NAME}" -p "${RIE_PORT}:8080" "${IMAGE_NAME}" >/dev/null &

echo "Waiting for lambda runtime..."
for _ in $(seq 1 30); do
  if curl -sS "http://127.0.0.1:${RIE_PORT}/2015-03-31/functions/function/invocations" -d '{}' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Starting local proxy on http://127.0.0.1:${PROXY_PORT}/predict-ocr"
python3 "./lambda/local_proxy.py" --port "${PROXY_PORT}" --rie-port "${RIE_PORT}"
