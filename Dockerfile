FROM python:3.10.4
# Addding requirements
COPY requirements.txt requirements.txt
RUN pip install -U pip && pip install -r requirements.txt --no-cache-dir
# Setting working directory
WORKDIR /home/sholex
RUN mkdir static
RUN mkdir state
RUN mkdir healthchecks
# Healthcheks
COPY healthchecks/gunicorn.py healthchecks/gunicorn.py
# Copying source
COPY LilSholex LilSholex
COPY templates templates
COPY manage.py manage.py
COPY persianmeme persianmeme
# Running
CMD gunicorn --workers=2 --bind=0.0.0.0:80 --error-logfile /dev/stderr -t 15 LilSholex.wsgi