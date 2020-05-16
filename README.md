# Little Sholex
A Project Containing Telegram API bots and small web apps .
# Included Projects
- Persian Meme
- Group Guard
- Anonymous Chat
- Support Bot
# Usage
1. Install Docker
2. Create a swarm
3. Create these swarm secrets : 
    - meme : Persian Meme Token
    - group : Group Guard Token
    - admin : Admin Panel URL
    - django : Django Secret Key
    - support : Support Bot Token
    - anonymous : Anonymous Chat Token
    - db_password : Database **root** password
3. `docker stack deploy -c docker-compose.yml {stack name}`

**Swarm health checks are included and containers will get replaced after running into a problem !**

**If you have any questions about docker swarm or secrets checkout Docker official documentation about
Docker swarm secrets : https://docs.docker.com/engine/swarm/secrets/**
- In order to update your stack use this command :

    `docker stack deploy -c docker-compose.yml {same name}`
# Developers
    Created by NitroZeus and RezFD
    
    Telegram : https://t.me/SholexTeam
    GitLab : https://gitlab.com/nitrozeus
    GitLab : https://gitlab.com/RezFD

SholexTeam &reg;