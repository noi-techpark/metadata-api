FROM python:3.8.13-alpine3.15

COPY requirements.txt ./
COPY app.py ./
COPY service-account.json ./

RUN pip install --no-cache-dir -r requirements.txt

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]
CMD ["app.py" ]