import requests
import json
from datetime import datetime

data=None
with open('../train_data.json') as f:
  data =json.dumps(json.load(f))

url = "https://testk8s-62z2ktinla-uc.a.run.app/job/create"

payload = {
        "docker_uri":"gcr.io/edustudent360/image_multiclass_train:latest",
        "job_id":"train-job-{}-{}".format("ques1",str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))),
        "command": ["python3","classifier_train.py",f"--data_dir={data}","--model_dir=gs://labellerr-models-v1/cl1/prj1/ques1",
        "--run_eagerly=false","--resize=false","--multi_worker=false","--epochs=50","--steps_per_epoch=10"]
    }
print (payload)
headers = {
    "Content-Type": "application/json"
    }

response = requests.post(url, headers=headers,data = json.dumps(payload))

print(response.text.encode('utf-8'))
assert response.status_code == 200, "Request to kubernetes api failed. Check logs."
# return response.text.encode(('utf-8'))