source ./env.sh

# Configure Docker to use gcloud as a credential helper
# gcloud auth login
# gcloud auth configure-docker

docker build -t ${APP_NAME} .

docker tag ${APP_NAME} gcr.io/${PROJECT_ID}/${APP_NAME}

docker push gcr.io/${PROJECT_ID}/${APP_NAME}

gcloud run deploy --project ${PROJECT_ID} ${SERVICE_NAME} --image gcr.io/${PROJECT_ID}/${APP_NAME} --region ${REGION}

gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --region=${REGION} \
  --member=allUsers \
  --role=roles/run.invoker
