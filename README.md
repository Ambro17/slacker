# Slacker
Utility bot for slack

## Run it with docker
```
$ git clone https://github.com/Ambro17/slacker.git
$ cd slacker
$ docker build -t slacker .
$ vim .env.sample # Edit with your credentials and rename to .env
$ docker run --env-file .env -it --rm -p 3000:3000 slacker
```