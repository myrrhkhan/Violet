# Vi

A handwriting to text converter.

## Instructions

Currently redoing the app from the ground up. Backend is not ready yet, frontend, go to client, run yarn install and yarn run dev

## Lambda Docker deploy

`server` is deprecated; deploy from `lambda` as a container image so Python deps are baked in.

1. Ensure Docker daemon is running and AWS CLI is authenticated.
2. Deploy/update Lambda:

```bash
FUNCTION_NAME=your-lambda-name AWS_REGION=us-east-1 ./lambda/deploy.sh
```

If the function does not exist yet, also pass `LAMBDA_ROLE_ARN`:

```bash
FUNCTION_NAME=your-lambda-name AWS_REGION=us-east-1 LAMBDA_ROLE_ARN=arn:aws:iam::<account-id>:role/<lambda-exec-role> ./lambda/deploy.sh
```
