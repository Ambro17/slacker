# Slacker
Slack bot for humans

## Run it with docker
```
$ git clone https://nambrosini@stash.corp.onapsis.com/scm/~nambrosini/onabot.git
$ cd slacker
$ vim .env.sample # Edit with your credentials rename to .env
$ docker-compose up
```
Or if you want to do it the old way:

```
#   Install dependencies
$ mkvirtualenv slacker -p /usr/bin/python3.6
$ pip install -r slacker/requirements_dev.txt
$ pip install -r task_queue/requirements_dev.txt

#  Initialize db
$ export FLASK_APP="slacker.app:create_app()"
$ flask init-db

#  Start bot
$ gunicorn -w 4 "slacker.app:create_app()" -b 0.0.0.0:3000 # Start bot server
$ redis-server start # Start redis server to dispatch tasks
$ cd task_queue && celery worker -A tasks --loglevel=info # Start worker
```

# Project Layout
```
.
├── slacker
│   ├── api
│   │   ├── aws
│   │   ├── feriados
│   │   ├── hoypido
│   │   ├── poll
│   │   ├── retro
│   │   ├── rooms
│   │   │   └── images
│   │   └── subte
│   ├── blueprints
│   │   ├── commands.py
│   │   ├── interactivity.py
│   │   ├── ovi_management.py
│   │   ├── retroapp.py
│   │   ├── rooms.py
│   │   └── stickers.py
│   └── models
│       ├── aws
│       ├── poll
│       ├── retro
│       └── stickers
├── task_queue
└── tests
    ├── api
    ├── blueprints
    └── models
```
The project uses Flask as a framework and follows the application factory pattern to ease testing and development.
Tests folder replicates the hierarchy on slacker dir.
Blueprints group bot functionality by topic. i.e Utilities for Retro Meetings have their own blueprint, commands have another one.
Ideally, all features that are more complex than a simple command with an api request should have a module on blueprints dir

## Commands:
`/feriados`

`/hoypido`

`/subte`

`/poll Who's the best football player ever? Messi, Lionel Messi, Lio`

## Retro Blueprint
`/add_team`

`/start_sprint`

`/add_retro_item`

`/show_retro_items`

`/end_sprint`

## Sticker Blueprint
`/add_sticker <name> <image_url>`

`/list_stickers`

`/send_sticker <name>`

# Tests
To run tests run pytest on the project dir.

`$ pytest`

# Future features
`/code`  Highlight code as monospace (or share a link to the snippet)

`/meet @user1 @user2`

`/on_home_office` - Set status to working for one day

`/not_available [hs]` - Set as not available to discourage interruptions

`/suscribe <subte_line>`

`/futbol <Dia>+` - Anotarse para el partido

`/paddle`

`/accountant`

`/challenge <ping_pong|play|metegol> @someone [optional_taunt]` - Send a private message challenging a rival


## Credits

Project layout was loosely inspired by [cookiecutter-flask](https://github.com/cookiecutter-flask/cookiecutter-flask)

Docker Compose was heavily inspired by the work of [mattkohl and itsrifat](https://github.com/mattkohl/docker-flask-celery-redis)

