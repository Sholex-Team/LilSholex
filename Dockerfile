FROM python:3.9.6
# Addding requirements
COPY requirements.txt requirements.txt
RUN pip install -U pip && pip install -r requirements.txt --no-cache-dir
# Setting working directory
WORKDIR /home/sholex
# Healthcheks
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
CMD gunicorn --workers=1 --threads=2 --bind=0.0.0.0:80 \
--access-logfile /dev/null --error-logfile /dev/stderr LilSholex.wsgi