# Vi

A handwriting to text converter.

## Instructions

Currently redoing the app from the ground up. Backend is not ready yet, frontend, go to client, run yarn install and yarn run dev

## Lambda Docker deploy

`server` is deprecated; deploy from `lambda` as a container image so Python deps are baked in.

1. Ensure Docker daemon is running and AWS CLI is authenticated.
2. Run the Lambda locally (localhost endpoint that mirrors API Gateway path):

```bash
./lambda/run-local.sh
```

This starts:
- local Lambda runtime on `http://127.0.0.1:9000`
- local proxy endpoint on `http://127.0.0.1:3001/predict-ocr`

In another terminal you can smoke test it:

```bash
./lambda/smoke-local.sh
```

To point the client to local mode, run Next.js with:

```bash
NEXT_PUBLIC_OCR_ENDPOINT=http://127.0.0.1:3001/predict-ocr yarn dev
```

3. Deploy/update Lambda:

```bash
FUNCTION_NAME=your-lambda-name AWS_REGION=us-east-1 ./lambda/deploy.sh
```

Optional: run local smoke test before push in deploy flow:

```bash
FUNCTION_NAME=your-lambda-name AWS_REGION=us-east-1 SMOKE_TEST_LOCAL=1 LOCAL_TEST_IMAGE=./client/testimg.jpg ./lambda/deploy.sh
```

If the function does not exist yet, also pass `LAMBDA_ROLE_ARN`:

```bash
FUNCTION_NAME=your-lambda-name AWS_REGION=us-east-1 LAMBDA_ROLE_ARN=arn:aws:iam::<account-id>:role/<lambda-exec-role> ./lambda/deploy.sh
```
