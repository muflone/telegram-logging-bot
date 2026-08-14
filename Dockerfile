FROM python:3.14.6-alpine3.24

WORKDIR /app
COPY . .
RUN python3 -m pip install -r requirements.txt

USER nobody:nobody
CMD ["python3", "./main.py"]
