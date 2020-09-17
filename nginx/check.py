import requests
try:
    if requests.get('https://bot.sholexteam.ir/').status_code != 200:
        exit(1)
except requests.RequestException:
    exit(1)
