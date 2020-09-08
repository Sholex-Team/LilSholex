import requests
try:
    if requests.get('http://localhost').status_code != 404:
        exit(1)
except requests.RequestException:
    exit(1)
