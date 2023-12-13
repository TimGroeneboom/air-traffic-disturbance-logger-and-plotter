#!/bin/bash

# For the following network creation to work you need to change the default subrange of the docker network
# See : https://serverfault.com/questions/916941/configuring-docker-to-not-use-the-172-17-0-0-range
# Create network
docker network create --subnet=172.17.0.0/16 omd-backend-network

# Fire up backend
docker create --name omd-backend --net omd-backend-network --ip 172.17.0.2 omd-backend

# Fire up database
docker create --name omd-database --net omd-backend-network --ip 172.17.0.3 omd-database
