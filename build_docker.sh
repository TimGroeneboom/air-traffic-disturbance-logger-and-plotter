#!/bin/bash
sudo docker build --tag air-traffic-logger-and-plotter . --build-arg PRIVATE_SSH_KEY="$(cat $HOME/.ssh/id_rsa)" --build-arg PORT=5000
