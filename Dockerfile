FROM alpine
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
COPY docker/start.sh /opt/docker/start.sh
RUN adduser -D deploy
RUN apk update
RUN apk upgrade
RUN apk --no-cache add \
    python3 \
    python3-dev \
    postgresql-client \
    postgresql-dev \
    build-base \
    gdal \
    libxml2-dev libxslt-dev \
    gettext jpeg-dev zlib-dev
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
RUN apk del -r python3-dev postgresql
ENV PYTHONUNBUFFERED 1
COPY . /app/
RUN chmod a+x /opt/docker/start.sh

ENTRYPOINT [ "/opt/docker/start.sh" ]