FROM ubuntu:18.04
RUN apt-get update && yes | apt-get upgrade
RUN apt-get install curl -y
RUN apt-get install -y gnupg2
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-sdk -y
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN cat /etc/apt/sources.list.d/nodesource.list
RUN apt -y install nodejs
RUN mkdir deployauto
COPY . deployauto
WORKDIR /deployauto
ENV GOOGLE_APPLICATION_CREDENTIALS='edustudent360-c1d02fe3adea.json'
RUN chmod +x cmds.sh
# Install production dependencies.
RUN npm install --only=production
# Run the web service on container startup.
CMD [ "npm", "start" ]
