import requests
try:
    if requests.get('http://localhost/').status_code == 200:
        exit(0)
except requests.RequestException:
    pass
exit(1)
