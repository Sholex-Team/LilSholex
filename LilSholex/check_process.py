import requests
import psutil
if (length := len(psutil.pids())) != 5:
    print(f'PIDs are {length}')
    exit(1)
try:
    if requests.get('http://localhost').status_code != 404:
        print('Request failed !')
        exit(1)
except requests.RequestException:
    exit(1)
