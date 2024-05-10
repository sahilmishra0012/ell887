# Image_Classification_Labellerr

## Entry Point Command:

```
python classifier_train.py --data_dir='/path_to_json_file/output2.json' --model_dir='gs://imgcls/Intel' --run_eagerly=true --resize=false --multi_worker=true --epochs=50 --steps_per_epoch=100
```

## NODE JS SUBSCRIBER FOR DEPLOYMENT
Change Path of service account json in Docker file 

Deploy it on cloud run with memory 1Gi and 1 cpu

Create the subscriber using cloud run endpoint and add /deploy route to the endpoint

Keep Acknowledgement limit to 300 Seconds to allow subscriber to pull image and model and deploy  both



## GCR Docker Image Pull Command:

```
docker pull gcr.io/aaria-263910/imgclsfinaltry:v1
```
## POSTMAN COLLECTION
Image Classification
Prediction on single image
key : image - IMAGE FILE
key : link - GCS MODEL LINK

