#!/usr/bin/env bash
set -euo pipefail

PROXY_URL="${LOCAL_PROXY_URL:-http://127.0.0.1:3001/predict-ocr}"
TEST_IMAGE="${LOCAL_TEST_IMAGE:-./client/testimg.jpg}"

if [[ ! -f "${TEST_IMAGE}" ]]; then
  echo "Test image not found: ${TEST_IMAGE}"
  exit 1
fi

echo "POST ${TEST_IMAGE} -> ${PROXY_URL}"
curl -sS -X POST "${PROXY_URL}" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@${TEST_IMAGE}"
echo
