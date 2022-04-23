# Little Sholex
A Project Containing Telegram API bots and small web apps .
# Included Projects
- [Persian Meme](https://t.me/Persian_Meme_Bot)
# Usage
1. Install Docker
2. Create a swarm
3. Create these docker swarm secrets: 
   - `persianmeme_token`: Persian Meme Telegram API token
   - `persianmeme_channel`: Persian Meme voting channel ID
   - `secret_key`: Django secret key
   - `db_password`: Database password
   - `persianmeme_anim`: Persian Meme help GIF file ID
   - `persianmeme_logs`: Persian Meme logging channel ID
   - `persianmeme_messages`: "Contact Admin" archive channel ID
   - `persianmeme_reports`: Meme Report archive channel ID
   - `ssl_certificate`: SSL certificate
   - `ssl_key`: SSL private key
   - `dhparam`: SSL dhparam
   - `domain`: Your Domain
   - `persianmeme_help_messages`: A JSON file containing help messages and animations
4. Replace {persianmeme_token} & {domain} inside conf/nginx.conf with
   your domain and bot token
5. `docker stack deploy -c docker-compose.yml {stack name}`

**Swarm health checks are included and containers will get replaced after running into a problem !**

**If you have any questions about docker swarm or secrets checkout Docker official documentation about
Docker swarm secrets: https://docs.docker.com/engine/swarm/secrets/**
- In order to update your stack use this command:

    `docker stack deploy -c docker-compose.yml {stack name}`
# Developers
Created by NitroZeus and RezFD
      
- Telegram: [@SholexTeam](https://t.me/SholexTeam)
- GitHub: [@RealNitroZeus](https://github.com/RealNitroZeus) - [@RezFD](https://github.com/RezFD)
- Email: [NitroZeus](mailto:NitroZeus@sholexteam.ir) - [RezFD](mailto:RezFD@sholexteam.ir)

SholexTeam &reg;
