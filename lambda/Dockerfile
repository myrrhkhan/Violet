FROM public.ecr.aws/lambda/python:3.10

ENV HF_HOME=/var/task/hf-cache
ENV TRANSFORMERS_CACHE=/var/task/hf-cache

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN mkdir -p "${HF_HOME}" && \
    python -c "from transformers import TrOCRProcessor, VisionEncoderDecoderModel; model_id='microsoft/trocr-base-handwritten'; TrOCRProcessor.from_pretrained(model_id, cache_dir='${HF_HOME}'); VisionEncoderDecoderModel.from_pretrained(model_id, cache_dir='${HF_HOME}')"

COPY lambda_function.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_function.lambda_handler"]
