#!/bin/bash

# Build the omd database mongo db docker container
sudo docker build --tag omd-database -f docker-omd-database .

# Build the omd backend web app container
sudo docker build --tag omd-backend -f docker-omd-backend . --build-arg PRIVATE_SSH_KEY="$(cat $HOME/.ssh/id_rsa)" --build-arg PORT=5000
