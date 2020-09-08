# Import Python
FROM python:3.8.5
# Installing requirements
ADD requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copying Source
WORKDIR /home/sholex
ADD LilSholex/LilSholex LilSholex
ADD LilSholex/manage.py manage.py
ADD LilSholex/check_process.py check_process.py
ADD LilSholex/persianmeme persianmeme
ADD LilSholex/templates templates
# Exposing Port
EXPOSE 80/tcp
# Running
CMD python manage.py makemigrations persianmeme && python manage.py migrate && python manage.py clear_tasks && \
python manage.py process_tasks --sleep 1.5 & daphne -b 0.0.0.0 -p 80 LilSholex.asgi:application