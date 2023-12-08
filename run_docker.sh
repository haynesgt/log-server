source env.sh

docker run --rm --name log-server -p 8080:8080 ${APP_NAME}:latest
