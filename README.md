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
   - `persianmeme_logs`: Persian Meme logging channel ID
   - `persianmeme_messages`: "Contact Admin" archive channel ID
   - `persianmeme_reports`: Meme Report archive channel ID
   - `ssl_certificate`: SSL certificate
   - `ssl_key`: SSL private key
   - `dhparam`: SSL dhparam
   - `domain`: Your Domain
   - `webhook_token`: Security token which Telegram will include in its webhook requests headers
   - `secrets/help_messages.json`: A JSON formatted file, containing help messages and animations
   - `secrets/email_config.json`: A JSON formatted file, containing error reporting email config.
   - `persianmeme_id`: Bot's numeric ID (used for identifying memes that are posted to the voting channel by the bot itself.)
4. Create/Edit these configs:
   - `conf/admins.json`: JSON formatted file, containing list of admins to whom internal errors are sent.
5. Replace {domain} inside conf/nginx.conf with your domain.
6. `docker stack deploy -c docker-compose.yml --with-registry-auth {stack name}`

**If you have any questions about docker swarm or secrets checkout Docker official documentation about
Docker swarm secrets: https://docs.docker.com/engine/swarm/secrets/**
- In order to update your stack use this command:

    `docker stack deploy -c docker-compose.yml --with-registry-auth {stack name}`
# Developers
Created by NitroZeus and RezFD
      
- Telegram: [@SholexTeam](https://t.me/SholexTeam)
- GitHub: [@RealNitroZeus](https://github.com/RealNitroZeus) - [@RezFD](https://github.com/RezFD)
- Email: [NitroZeus](mailto:NitroZeus@sholex.team) - [RezFD](mailto:rez@sholex.team)

SholexTeam &reg;
