APP='gateway-manager'
VERSION='latest'
IMAGE_REPO='ehealthafrica'

docker tag ${APP} "${IMAGE_REPO}/${APP}:${VERSION}"
docker push "${IMAGE_REPO}/${APP}:${VERSION}"
