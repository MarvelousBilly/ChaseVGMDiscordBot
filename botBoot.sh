#!/bin/bash
sleep 60
/usr/bin/env -i HOME=/home/mia USER=mia PATH=/usr/bin:/bin:/usr/local/bin \
    /usr/bin/python -u /home/mia/discord.py/discordBot.py 2>&1 | tee -a /home/mia/discord.py/logs