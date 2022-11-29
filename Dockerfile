FROM python:3.11.0

# Setting working directory
WORKDIR /home/sholex
RUN mkdir static
RUN mkdir state
RUN mkdir healthchecks

# Addding requirements
COPY requirements.txt requirements.txt
RUN pip install -U pip && pip install -r requirements.txt --no-cache-dir

# Healthcheks
COPY healthchecks/gunicorn.py healthchecks/gunicorn.py

# Copying source
COPY LilSholex LilSholex
COPY templates templates
COPY manage.py manage.py
COPY persianmeme persianmeme

# Running
CMD gunicorn --workers=2 --threads=2 --keep-alive=200 --bind=0.0.0.0:80 -t 10 LilSholex.wsgi