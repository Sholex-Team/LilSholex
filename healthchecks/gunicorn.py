import requests
try:
    if requests.get('http://localhost:8080/').status_code == 404:
        exit(0)
except requests.RequestException:
    pass
exit(1)
