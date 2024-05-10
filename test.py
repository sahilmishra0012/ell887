from google.cloud import storage
from google.oauth2 import service_account


def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"
    credentials = service_account.Credentials.from_service_account_file('/home/samkiller007/Desktop/autolabel-287715-bff75ec03073.json')


    storage_client = storage.Client(credentials=credentials)

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)

    blob_list = []
    for blob in blobs:
        blob_list.append(blob.name)
    
    return blob_list


data = list_blobs('image_multiclass')
for i in data[1:-1]:
    print(i.split('/')[1].split('_')[7])


records = []

for i in data[1:-1]:
    dic= dict()
    dic['file_name'] = i.split('/')[1]
    dic['label'] = i.split('/')[1].split('_')[7]
    records.append(dic)
    
print(records)

import json
with open('data.json', 'w') as f:
    json.dump(records, f)
