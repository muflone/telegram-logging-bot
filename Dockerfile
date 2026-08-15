FROM python:3.14.6-alpine3.24

WORKDIR /app
RUN apk update && \
    apk add font-noto-cjk
COPY . .
RUN python3 -m pip install -r requirements.txt

USER nobody:nobody
CMD ["python3", "./main.py"]
