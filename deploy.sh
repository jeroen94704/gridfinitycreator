#!/bin/bash

docker-compose --env-file ./.env.container up --build --force-recreate --no-deps -d
