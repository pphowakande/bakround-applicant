#!/usr/bin/env python3

from __future__ import print_function

__author__ = "natesymer"

import os
import sys
import json
import boto3
from botocore.exceptions import ClientError

def deploy(family,
           containers=[],
           cpu=None,
           memory=None,
           is_fargate=True,
           network_mode='awsvpc',
           volumes=[],
           cluster=None,
           service=None,
           count=1,
           min_healthy=0,
           max_healthy=200):
    try:
        client = boto3.client('ecs', region_name=os.getenv("AWS_REGION"))
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    container_defs = []
    for (name, image, portMappings, environ) in containers:
        env = []
        for k, v in (environ or {}).items():
            env.append({"name": k, "value": v})

        container_defs.append({
            'portMappings': portMappings,
            'essential': True,
            'name': name,
            'image': image,
            'environment': env
        })

    execution_role_arn = "arn:aws:iam::683224132562:role/ecsTaskExecutionRole"

    try:
        # http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.register_task_definition
        response = client.register_task_definition(
            executionRoleArn=execution_role_arn,
            taskRoleArn=execution_role_arn,
            family=family,
            containerDefinitions=container_defs,
            requiresCompatibilities=["FARGATE" if is_fargate else "EC2"],
            networkMode=network_mode,
            cpu=str(cpu) if cpu else None,
            memory=str(memory) if memory else None,
            volumes=volumes
        )

        if not response:
            return False

        try: task_definition = response['taskDefinition']['taskDefinitionArn']
        except: return False

        # http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.update_service
        return client.update_service(
            cluster=cluster,
            service=service,
            desiredCount=count,
            taskDefinition=task_definition,
            deploymentConfiguration={
                # more information on the max and min healthy percentages can be found here:
                # http://docs.aws.amazon.com/AmazonECS/latest/developerguide/update-service.html
                'maximumPercent': max_healthy,
                'minimumHealthyPercent': min_healthy
            }
        )
    except ClientError as err:
        print("ECS error: {}".format(str(err)))
        return False

def get_config(key):
    try:
        client = boto3.client('s3', region_name=os.getenv("AWS_REGION"))
    except ClientError as err:
        print("S3 Error: {}".format(str(err)))
        return None

    try:
        return client.get_object(Bucket='applicant-configuration', Key=key)['Body'].read()
    except ClientError as err:
        print("S3 Error: {}".format(str(err)))
        return None

def pt_host(d, hostname):
    d['PAPERTRAIL_HOSTNAME'] = hostname
    return d

def main():
    DJANGO_IMAGE=os.getenv('DJANGO_IMAGE')
    SERVICES_IMAGE=os.getenv('SERVICES_IMAGE')
    REDIS_IMAGE="redis:5.0.0-alpine"

    django_ports = [
        {
            "hostPort": 8000,
            "protocol": "tcp",
            "containerPort": 8000
        }
    ]

    # dev_env = json.loads(get_config("env-dev.json"))
    production_env = json.loads(get_config("env-prod.json"))

    service_ports = []

    redis_ports = [
        {
          "hostPort": 6379,
          "protocol": "tcp",
          "containerPort": 6379
        }
    ]
    
    # deploy("bakround-dev",
    #        containers=[("django", DJANGO_IMAGE, django_ports, pt_host(dev_env, 'bakround-dev-django')),
    #                    ("services", SERVICES_IMAGE, service_ports, pt_host(dev_env, 'bakround-dev-services')),
    #                    ("redis", REDIS_IMAGE, redis_ports, {})],
    #        cluster="bakround",
    #        service="bakround-dev",
    #        memory=4096,
    #        cpu=2048)
    deploy("bakround-prod-django",
           containers=[("django", DJANGO_IMAGE, django_ports, pt_host(production_env, 'bakround-prod-django')),
                       ("redis", REDIS_IMAGE, redis_ports, {})],
           cluster="bakround",
           service="bakround-prod-django",
           memory=4096,
           cpu=2048)
    deploy("bakround-prod-services",
           containers=[("services", SERVICES_IMAGE, service_ports, pt_host(production_env, 'bakround-prod-services')),
                       ("redis", REDIS_IMAGE, redis_ports, {})],
           cluster="bakround",
           service="bakround-prod-services",
           memory=8192,
           cpu=4096)

if __name__ == "__main__":
    main()
