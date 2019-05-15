FROM ubuntu:18.04

########################################################### ENVIRONMENT: base ################################################
USER root

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv
RUN python3.6 -m pip install pip --upgrade

########################################################### Application needed: ################################################

COPY requirements.txt ./
RUN pip install -r requirements.txt
ADD ./ /app
WORKDIR /app
