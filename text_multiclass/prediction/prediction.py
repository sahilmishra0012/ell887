'''
Script for Predictions
'''
import os
from datetime import datetime
import uuid
import tensorflow as tf
import numpy as np
from google.cloud import storage


model = None

def read_jpg(file, shape, file_name=None):

    '''Function to read JPEG Images from GCP GCS bucket.

        Parameters:
            path        - Image files path.
            shape       - Image Shape.
        Return Value:
            Processed image and label tensors.
    '''
    file_name = '{}-{}.jpg'.format(uuid.uuid1(), str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))

    file_path = tf.keras.utils.get_file(file_name, file)
    image = tf.io.read_file(file_path)
    image = tf.io.decode_jpeg(image)
    image = tf.image.resize(image, [shape, shape], preserve_aspect_ratio=True, method='nearest')
    s = tf.shape(image)
    paddings = [[0, m-s[i]] for (i, m) in enumerate([shape, shape, 3])]
    image = tf.pad(image, paddings, mode='CONSTANT', constant_values=-1)
    image.set_shape((shape, shape, 3))
    return image


def load_preprocess_data(json_data):

    '''Function to read image paths and load images.

        Parameters:
            files        - List of image files paths for predictions.
        Return Value:
            List of image arrays.
    '''
    for i in range(0,len(json_data['records'])):
        json_data['records'][i]['data']=read_jpg(json_data['records'][i]['fileLink'], 224,file_name=json_data['records'][i]['fileId'])
    return json_data


def download_and_load_model(model_path):

    '''Function to read model path, download and load_model.

        Parameters:
            model_path        - Model path of latest model.
        Return Value:
            Model Loading Status.
    '''

    global model
    splits = model_path.split('/')
    bucket_name = splits[2]
    dir_name = ""
    for i in splits[3:]:
        dir_name = dir_name+"/"+i
    print(dir_name[1:])
    if not os.path.exists('/'.join(splits[-2:])):
        storage_client = storage.Client()
        blobs = storage_client.list_blobs(bucket_name, prefix=dir_name[1:])
        for blob in blobs:
            filename = blob.name
            print(filename)
            if filename.rsplit('/')[-1] != '':
                create_dir = filename.split(splits[-2])[1]
                os.makedirs(splits[-2]+os.path.dirname(create_dir),mode=0o777, exist_ok=True)
                blob.download_to_filename(splits[-2]+filename.split(splits[-2])[1])  # Download
        print("Model Downloaded")
    else:
        print("Model Already Downloaded")
    try:
        if model is None:
            model = tf.keras.models.load_model('/'.join(splits[-2:]))
            return "Model Loaded"
        else:
            return "Model already in memory"
    except:
        return "Model Loading Failed"


def predict_on_data(json_data):

    '''Function to make predictions.

        Parameters:
            data        - List of image arrays for predictions.
        Return Value:
            List of predictions.
    '''

    global model
    
    for i in range(0,len(json_data['records'])):
        json_data['records'][i]['predictions'] = model.predict(np.expand_dims(json_data['records'][i]['data'], axis=0)).tolist()
        json_data['records'][i].pop('data')
    return json_data
