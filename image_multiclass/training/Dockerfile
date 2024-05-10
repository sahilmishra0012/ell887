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
ENV GOOGLE_APPLICATION_CREDENTIALS=autolabel-287715-bff75ec03073.json
ENV DB_USER=pjinx
ENV DB_PASS=43erdfcghu890@uyh
ENV DB_NAME=labellerr
RUN apt-get install wget -y 
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
RUN chmod +x cloud_sql_proxy
RUN mkdir /cloudsql; chmod 777 /cloudsql
