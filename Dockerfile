# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}
COPY processor.py ${LAMBDA_TASK_ROOT}
COPY clients.py ${LAMBDA_TASK_ROOT}
COPY logging_config.py ${LAMBDA_TASK_ROOT}
COPY utils.py ${LAMBDA_TASK_ROOT}
COPY cloudflare_handler.py ${LAMBDA_TASK_ROOT}
COPY config/ ${LAMBDA_TASK_ROOT}/config/

# Copy bs modules
COPY bs/ ${LAMBDA_TASK_ROOT}/bs/

# Set the CMD to your handler
CMD ["lambda_handler.lambda_handler"]
