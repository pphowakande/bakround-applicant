#!/usr/bin/env python3

import boto3
import os
from base64 import b64decode
from subprocess import Popen, PIPE

client = boto3.client('ecr', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                             region_name=os.getenv("AWS_REGION"))
response = client.get_authorization_token()

# since we don't supply registry ids, AWS will return only one element
# representing the default ECR registry
token = response['authorizationData'][0]
auth_token = b64decode(token['authorizationToken']).decode()
username, password = auth_token.split(':')
command = ['docker', 'login', '-u', username, '--password-stdin', token['proxyEndpoint']]

p = Popen(command, stdin=PIPE)
p.communicate(input=password.encode('utf-8'))

