source ./env.sh

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

./build_docker.sh

# test if repo exists
aws ecr describe-repositories --repository-names ${APP_NAME} > /dev/null 2>&1
if [ $? -ne 0 ]
then
    echo "Repository ${APP_NAME} does not exist. Creating..."
    aws ecr create-repository --repository-name ${APP_NAME}
fi

# Authenticate Docker to the ECR registry
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Tag your image to match the repository name
docker tag ${APP_NAME}:latest ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${APP_NAME}:latest

# Push the image to ECR
docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${APP_NAME}:latest
