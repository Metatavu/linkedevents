FROM python:3.7.4
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
COPY docker/start.sh /opt/docker/start.sh
COPY docker/local_settings.py /app/
ENV PYTHONUNBUFFERED 1

RUN apt-get update 
RUN apt-get install --no-install-recommends -y gdal-bin python-gdal python3-gdal nginx
RUN pip3 install gunicorn

RUN rm -f /etc/nginx/sites-enabled/default
COPY docker/nginx.conf /etc/nginx/sites-enabled/default

RUN pip3 install -r requirements.txt
COPY . /app/
RUN chmod a+x /opt/docker/start.sh

EXPOSE 8000

ENTRYPOINT [ "/opt/docker/start.sh" ]