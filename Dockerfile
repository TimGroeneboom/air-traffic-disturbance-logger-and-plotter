# syntax=docker/dockerfile:1

# Install python3, ubuntu and mongo
FROM python:3.10-slim-buster
FROM ubuntu:22.04
FROM mongo:latest

# Update aptitude with new repo
RUN apt-get update

# Install git 
RUN apt-get install -y git

# Set port as environment variable
ENV PORT=5000

# Set amount of workers
ARG WORKERS=0
ENV WORKERS=$WORKERS

# Authorize SSH Host
ARG PRIVATE_SSH_KEY
RUN mkdir -p /root/.ssh && \
    chmod 0700 /root/.ssh && \
    ssh-keyscan github.com > /root/.ssh/known_hosts && \
    # Add the keys and set permissions
    echo "$PRIVATE_SSH_KEY" > /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa

# Install pip3
RUN apt-get -y install python3-pip

# Install requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Remove SSH keys
RUN rm -rf /root/.ssh/

# Set up nginx
RUN apt-get install -y nginx

# Copy nginx config file
COPY nginx.conf /etc/nginx/sites-available/default

# Set timezone
ENV TZ="Europe/Amsterdam"

# Copy contents
COPY . .

# Init mongo database
ARG DATABASE_NAME="planelogger"
ENV DATABASE_NAME=$DATABASE_NAME
ARG COLLECTION_NAME="states"
ENV COLLECTION_NAME=$COLLECTION_NAME
ARG LAT_LON_CACHE_NAME="latloncache"
ENV LAT_LON_CACHE_NAME=$LAT_LON_CACHE_NAME

RUN mongod --fork --logpath /var/log/mongodb.log && \
    mongosh $DATABASE_NAME --eval "db.createCollection('$COLLECTION_NAME')" && \
    mongosh $DATABASE_NAME --eval "db.createCollection('$LAT_LON_CACHE_NAME')"

# Expose ports
EXPOSE 80

# Run web app
CMD mongod --fork --logpath /var/log/mongodb.log && \
    service nginx start && \
    gunicorn -b 0.0.0.0:$PORT wsgi:application -w \
    "$(if [ $WORKERS = 0 ] ; then echo $(($(grep -c ^processor /proc/cpuinfo)*2+1)) ; else echo '$WORKERS'; fi)"