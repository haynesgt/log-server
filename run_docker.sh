source env.sh

docker run --rm --name log-server -p 8000:8000 ${APP_NAME}:latest
