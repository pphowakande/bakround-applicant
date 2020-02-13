FROM alpine:3.8

COPY ./requirements /requirements
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# N.B. postgresql-dev takes care of installing libressl

RUN apk add build-base \
 && apk add --no-cache gcc python3-dev musl-dev tor supervisor python3 libffi-dev libxml2-dev libxslt-dev jpeg jpeg-dev libpq \
 && apk add --no-cache --repository http://dl-2.alpinelinux.org/alpine/v3.8/main postgresql-dev=10.10-r0 \
 && python3 -m ensurepip && rm -r /usr/lib/python*/ensurepip \
 && apk add --no-cache --virtual .pynacl_deps build-base python3-dev libffi-dev \
 && pip3 install --upgrade pip setuptools \
 && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip; fi \
 && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi

RUN pip install -r /requirements/local.txt

WORKDIR /app
EXPOSE 8000
CMD ["supervisord", "--configuration", "/app/compose/django/supervisor.conf"]
