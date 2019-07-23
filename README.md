# Slacker
Utility bot for slack

## Run it with docker
```
$ git clone https://nambrosini@stash.corp.onapsis.com/scm/~nambrosini/onabot.git
$ cd slacker
$ vim .env.sample # Edit with your credentials rename to .env
$ docker-compose up
```
Or if you want to do it manually:
```
$ redis-server  # Start redis server
$ gunicorn -w 4 "slacker:create_app()" -b 0.0.0.0:3000 # Start bot server
$ cd task-queue && celery worker -A tasks --loglevel=info # Start worker
```

# Project Layout
```
├── slacker
│   ├── api
│   │   ├── aws
│   │   ├── feriados
│   │   ├── hoypido
│   │   ├── retro
│   │   ├── stickers
│   │   └── subte
│   ├── blueprints
|   |   ├── commands.py
│   │   ├── interactivity.py
│   │   ├── ovi_management.py
│   │   ├── retroapp.py
│   │   └── stickers.py
│   └── models
│       ├── aws
│       ├── poll
│       ├── retro
│       └── stickers
└── tests
    ├── api
    ├── blueprints
    └── models
```
The project uses Flask as a framework and follows the application factory pattern to ease testing and development.
Tests folder replicates the hierarchy on slacker dir.
Blueprints group bot functionality by topic. i.e Utilities for Retro Meetings have their own blueprint, commands have another one. Ideally, all features that are more complex than a simple command with an api request should have a module on blueprint.

## Commands:
`/aws_register` - hola

`/feriados [n]`

`/feriado`

`/hoypido`

`/subte`

`/poll Who's the best football player ever? Messi Lionel LioMessi`
## Retro Blueprint
`/add_team`

`/start_sprint`

`/add_retro_item`

`/show_retro_items`

`/end_sprint`
## Sticker Blueprint
`/add_sticker <name> <image_url>`

`/list_stickers`

`/sticker <name>`
## Ovi Blueprint
`/ovi_register` - Fill ovi form

`/ovi <start|stop|info|redeploy> <vm_alias>`

# Tests
To run tests just run pytest on the project dir.

`$ pytest`

# Future features

`/futbol_estoy <Dia>+` - Anotarse para el partido

`/paddle`

`/accountant`

`/challenge <ping_pong|play|metegol> @someone [optional_taunt]` - Send a private message challenging a rival

`/code <snippet>` - Highlight code as monospace (or share a link to the snippet)

`/rooms` - List all available rooms (To ease reservations for meetings!)

`/room <name>` - Get location of meeting room

`/on_home_office` - Set status to working for one day

`/not_available [hs]` - Set as not available to discourage interruptions

`/suscribe <subte_line>`


## Credits

Project layout was loosely inspired by [cookiecutter-flask](https://github.com/cookiecutter-flask/cookiecutter-flask)

Docker Compose was heavily inspired by the work of [mattkohl and itsrifat](https://github.com/mattkohl/docker-flask-celery-redis)

