FROM python:3.11.6-slim

WORKDIR /app

COPY Pipfile* /app/

RUN pip install pipenv && pipenv install --system --deploy

COPY . /app

CMD [ "bash", "-c", "gunicorn -w 1 -t 2 --graceful-timeout 1 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker log_server.api:app" ]
# same bash command:
# gunicorn -w 1 -t 2 --graceful-timeout 1 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker log_server.api:app
