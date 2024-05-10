FROM ubuntu:xenial

# Install manually TensorflowServing
RUN apt-get update && \
  apt-get install -y curl && \
  echo "deb http://storage.googleapis.com/tensorflow-serving-apt stable tensorflow-model-server tensorflow-model-server-universal" | tee /etc/apt/sources.list.d/tensorflow-serving.list && \
  curl https://storage.googleapis.com/tensorflow-serving-apt/tensorflow-serving.release.pub.gpg | apt-key add - && \
  apt-get update && \
  apt-get install tensorflow-model-server && \
  apt-get install -y python3 python3-pip

# set the working directory in the container to /app
WORKDIR /home

# add the current directory to the container as /app
ADD . /home

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt 

ENV GOOGLE_APPLICATION_CREDENTIALS='/home/edustudent360-c1d02fe3adea.json'

ENV MODEL_BASE_PATH='/home'  

# Serve the model on REST API port define by Cloud Run
#CMD python3 pull_model.py --gcs_bucket=${gcs_bucket} --gcs_subdir=${gcs_subdir} --model_name=${MODEL_NAME} && tensorflow_model_server --port=8500 --rest_api_port=${PORT} --model_name=${MODEL_NAME} --model_base_path=${MODEL_BASE_PATH}/${MODEL_NAME}
