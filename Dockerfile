# Import Python
FROM python:3.8.3
# Installing requirements
ADD requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copying Source
WORKDIR /home/sholex
ADD LilSholex/LilSholex LilSholex
ADD LilSholex/manage.py manage.py
ADD LilSholex/check_process.py check_process.py
ADD LilSholex/anonymous anonymous
ADD LilSholex/groupguard groupguard
ADD LilSholex/movie movie
ADD LilSholex/number number
ADD LilSholex/persianmeme persianmeme
ADD LilSholex/templates templates
ADD LilSholex/support support
# Exposing Port
EXPOSE 80/tcp
# Running
CMD python manage.py makemigrations movie groupguard support persianmeme anonymous && python manage.py migrate && \
python manage.py process_tasks --sleep 1.5 & \
gunicorn -b 0.0.0.0:80 --timeout 86400 --workers 1 --threads 4 --access-logfile \
/dev/stdout --error-logfile /dev/stderr --reload LilSholex.wsgi