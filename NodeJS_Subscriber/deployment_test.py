from google.cloud import pubsub
import json

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path('edustudent360', 'autolabeldev')

dic = {
    'gcppid': 'edustudent360',
    'gcsb': 'labellerr-models-v1',
    'gcsdir': 'cl1/prj1/ques1',
    'dport': 8501,
    'modelname': 'ques1',
    'modelpath': '/home',
    'labellerrpid': 'labeller21221',
    'quesid': 'ques1',
    'region': 'us-central1',
    'image_path': 'gcr.io/edustudent360/image_multiclass:v1'
}
data = str(json.dumps(dic))
future = publisher.publish(topic_path, data=data.encode("utf-8"))