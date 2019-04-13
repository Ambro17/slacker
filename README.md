# Slacker
Utility bot for slack

## Run it with docker
```
$ git clone https://github.com/Ambro17/slacker.git
$ cd slacker
$ docker build -t slacker .
$ docker run --env-file .env -it --rm -p 3000:3000 slacker
```

> `.env` file must define `SLACK_SIGNATURE`, `APP_TOKEN` and `BOT_TOKEN` env variables.
