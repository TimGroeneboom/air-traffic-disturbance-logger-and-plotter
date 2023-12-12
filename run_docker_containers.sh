#!/bin/bash

# First create network, this can fail if it already exists
docker network create --subnet=172.20.0.0/16 omd-network

# Fire up database
docker run --net omd-network --name omd_database --ip 172.20.0.10 -d omd-database

# Fire up backend
docker run --net omd-network --name omd_backend --ip 172.20.0.11 omd-backend
