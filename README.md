# Little Sholex
A Project Containing Telegram API bots and small web apps .
# Included Projects
- [Persian Meme](http://t.me/Persian_Meme_Bot)
# Usage
1. Install Docker
2. Create a swarm
3. Create these swarm secrets : 
   - persianmeme_token : Persian Meme Telegram API token
   - persianmeme_channel : Persian Meme voting channel ID
   - secret_key : Django secret key
   - db_password : Database password
   - persianmeme_anim : Persian Meme help GIF file ID
   - persianmeme_logs : Persian Meme logging channel ID
   - persianmeme_messages : Use anything not complete yet :)
   - ssl_certificate : SSL certificate
   - ssl_key : SSL private key
   - dhparam : SSL dhparam
4. `docker stack deploy -c docker-compose.yml {stack name}`

**Swarm health checks are included and containers will get replaced after running into a problem !**

**If you have any questions about docker swarm or secrets checkout Docker official documentation about
Docker swarm secrets : https://docs.docker.com/engine/swarm/secrets/**
- In order to update your stack use this command :

    `docker stack deploy -c docker-compose.yml {stack name}`
# Developers
    Created by NitroZeus and RezFD
    
    Telegram : https://t.me/SholexTeam
    GitLab : https://gitlab.com/nitrozeus
    GitLab : https://gitlab.com/RezFD

SholexTeam &reg;
