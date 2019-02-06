FROM python:3.7-alpine3.8
WORKDIR /app
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
RUN apk add --no-cache su-exec
COPY ./app /app
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-u", "app.py"]
