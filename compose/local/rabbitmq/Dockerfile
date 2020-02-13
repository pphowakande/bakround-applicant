FROM rabbitmq:3.7-management-alpine

ENV RABBITMQ_CONFIG_FILE /etc/rabbitmq/myconfig.conf
COPY ./rabbitmq.config /etc/rabbitmq/myconfig.conf
RUN chown rabbitmq:rabbitmq /etc/rabbitmq/myconfig.conf
