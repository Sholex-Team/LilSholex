FROM python:3.9.2
# Addding requirements
COPY requirements.txt requirements.txt
RUN pip install -U pip && pip install -r requirements.txt --no-cache-dir
# Exposing Ports
EXPOSE 8080/tcp
EXPOSE 8081/tcp
# Setting working directory
WORKDIR /home/sholex
# Healthcheks
COPY healthchecks/daphne.py healthchecks/daphne.py
COPY healthchecks/gunicorn.py healthchecks/gunicorn.py
# Adding Static Directory
RUN mkdir static
# Copying source
COPY LilSholex LilSholex
COPY templates templates
COPY manage.py manage.py
COPY persianmeme persianmeme
# Setting Volumes
VOLUME /home/sholex/persianmeme/migrations
# Running
CMD daphne -b 0.0.0.0 -p 8081 LilSholex.asgi:application