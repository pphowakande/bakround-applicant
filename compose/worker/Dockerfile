FROM alpine:3.8

COPY ./requirements /requirements

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app"


RUN apk add --no-cache --repository http://dl-2.alpinelinux.org/alpine/v3.8/main postgresql-dev=10.10-r0 \
 && apk add --no-cache --repository http://dl-2.alpinelinux.org/alpine/v3.8/community chromium===68.0.3440.75-r0 chromium-chromedriver===68.0.3440.75-r0 \
 && apk add --no-cache gcc python3-dev musl-dev tor supervisor python3 libffi-dev libxml2-dev libxslt-dev jpeg jpeg-dev libpq \
 && mkdir -p /var/lib/tor \
 && apk add build-base \
 && chown root:root /var/lib/tor \
 && apk add --no-cache --virtual .pynacl_deps build-base python3-dev libffi-dev \
 && python3 -m ensurepip && rm -rf /usr/lib/python*/ensurepip \
 && pip3 install --upgrade pip setuptools \
 && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip; fi \
 && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi

RUN pip install -r /requirements/local.txt

WORKDIR /app
CMD ["supervisord", "--configuration", "/app/compose/worker/supervisor.conf"]
