FROM python:3.13.2

# Setting working directory
WORKDIR /home/sholex
RUN mkdir static
RUN mkdir state

# Addding requirements
COPY requirements.txt requirements.txt
RUN pip install -U pip && pip install -r requirements.txt --no-cache-dir

# Copying source
COPY LilSholex LilSholex
COPY templates templates
COPY manage.py manage.py
COPY persianmeme persianmeme

# Running
CMD uvicorn --lifespan off --timeout-keep-alive 200 --host 0.0.0.0 --port 80 --timeout-graceful-shutdown 10 LilSholex.asgi:application