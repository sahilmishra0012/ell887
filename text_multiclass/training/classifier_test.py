import requests
import json
from datetime import datetime
import classifier_train

data=None
with open('../k8s_train_api/train_data.json') as f:
  data = json.dumps(json.load(f))

import os

os.system("python3 classifier_train.py --data_dir='{}' --model_dir=gs://labellerr-models-v1/cl1/prj1/ques1\
   --run_eagerly=false --resize=false --multi_worker=false --epochs=50 --steps_per_epoch=10".format(data))

