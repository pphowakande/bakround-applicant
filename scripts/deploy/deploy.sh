#!/bin/sh

# deploy.sh
# Deploy Bakround to prod and dev environments
# Dependencies:
#   python3
#   boto3
#   npm
#   docker

BUILD_VERSION=$(git rev-parse HEAD)
AWS_ACCOUNT_ID=683224132562
AWS_REGION=us-east-1

function make_docker_tag() {
    echo $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$1:$BUILD_VERSION
}

function build_app_docker_image() {
    DOCKERFILE=$1
    NAME=$2

    cp $DOCKERFILE .

    cat <<EOF >> ./Dockerfile
RUN wget https://github.com/papertrail/remote_syslog2/releases/download/v0.20/remote_syslog_linux_amd64.tar.gz -O remote_syslog.tar.gz \
 && tar -xvf remote_syslog.tar.gz \
 && cp remote_syslog/remote_syslog /remote_syslog2 \
 && rm -rf ./remote_syslog/ ./remote_syslog.tar.gz \
 && apk --no-cache add logrotate \
 && echo "*/5 *	* * *	/usr/sbin/logrotate /app/compose/common/logrotate.conf" >> /etc/crontabs/root \
 && mkdir -p /var/log/rotated/

ADD . /app

RUN printf '\n\n[include]\nfiles = /app/compose/common/prod_supervisor.conf\n' >> /app/compose/worker/supervisor.conf \
 && printf '\n\n[include]\nfiles = /app/compose/common/prod_supervisor.conf\n' >> /app/compose/django/supervisor.conf \
 && sed -i 's/stdout_logfile=.*/stdout_logfile=\/var\/log\/app-stdout.log/' /app/compose/worker/supervisor.conf \
 && sed -i 's/stderr_logfile=.*/stderr_logfile=\/var\/log\/app-stderr.log/' /app/compose/worker/supervisor.conf \
 && sed -i 's/stdout_logfile=.*/stdout_logfile=\/var\/log\/app-stdout.log/' /app/compose/django/supervisor.conf \
 && sed -i 's/stderr_logfile=.*/stderr_logfile=\/var\/log\/app-stderr.log/' /app/compose/django/supervisor.conf \
 && rm -rf /var/lib/apt/lists/* /var/cache/apk/* /usr/share/man /tmp/* /root/.cache
EOF

    sed -i -e 's/local.txt/production.txt/g' ./Dockerfile
    docker build -t $NAME:$BUILD_VERSION .
    rm ./Dockerfile
    docker tag $NAME:$BUILD_VERSION $(make_docker_tag $NAME)
}

npm update --dev
npm ci
npm run build-production

./scripts/deploy/ecr_login.py

build_app_docker_image "compose/worker/Dockerfile" "bakround/services"
build_app_docker_image "compose/django/Dockerfile" "bakround/django"

export DJANGO_IMAGE=$(make_docker_tag "bakround/django")
export SERVICES_IMAGE=$(make_docker_tag "bakround/services")

docker push $DJANGO_IMAGE
docker push $SERVICES_IMAGE

./scripts/deploy/ecs_deploy.py
