FROM ubuntu:18.04
RUN apt-get update && yes | apt-get upgrade
RUN apt-get install -y git python3-pip
RUN python3 -m pip install --upgrade pip
RUN mkdir imgcls
COPY . imgcls
WORKDIR /imgcls
RUN ls -a
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
ENV GOOGLE_APPLICATION_CREDENTIALS=credentials.json
