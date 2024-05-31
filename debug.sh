#!/bin/bash

docker-compose --env-file ./.env.container -f docker-compose.debug.yml up -d --build
