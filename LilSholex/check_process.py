import subprocess
import requests
if (result := len(subprocess.check_output(
        'ps -Af | grep "python manage.py process_tasks --sleep 1.5"', shell=True
).decode().strip().split('\n'))) != 4:
    exit(1)
try:
    if requests.get('http://localhost/').status_code != 200:
        exit(1)
except requests.RequestException:
    exit(1)
