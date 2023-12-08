FROM python:3.11.6-slim

WORKDIR /app

COPY Pipfile* /app/

RUN pip install pipenv && pipenv install --system --deploy

COPY . /app

ARG PORT=8080
ENV PORT ${PORT}

CMD [ "bash", "-c", "gunicorn -w 1 -t 2 --graceful-timeout 1 -b 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker log_server.api:app" ]
