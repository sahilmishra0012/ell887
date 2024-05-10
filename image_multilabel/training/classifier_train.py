"""
Script to train the model.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import warnings
import os
import gc
import json
from collections import namedtuple
from google.cloud import pubsub
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, LambdaCallback
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
from google.oauth2 import service_account
from models import InceptionV3Model
import data_factory
warnings.filterwarnings("ignore")

global best_binary_accuracy
best_binary_accuracy = -10


def epoch_end(epoch, logs):
    '''Function to save and upload model to GCS bucket and send Pub/Sub messages on ModelCheckpoint.
        Parameters:
            epoch   - The epoch while training the model
            logs    - The logs of metrics and losses during training
        Return Value:
            None
    '''

    storage_client = storage.Client()

    global best_binary_accuracy

    splits = param.model_dir.split('/')

    bucket_name = splits[2]
    dir_name = ""
    for i in splits[3:-1]:
        dir_name = dir_name+"/"+i
    dir_name = dir_name[1:]
    model_name = splits[-1]

    if best_binary_accuracy < logs['val_binary_accuracy']:
        best_binary_accuracy = logs['val_binary_accuracy']
        modelpath = sorted(os.listdir('Model'))[-1]
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(dir_name+'/'+model_name+'/' +
                           modelpath+'/saved_model.pb')
        blob.upload_from_filename('Model/'+modelpath+'/saved_model.pb')
        for i in os.listdir('Model/'+modelpath+'/variables'):
            blob = bucket.blob(dir_name+'/'+model_name +
                               '/'+modelpath+'/variables/'+i)
            blob.upload_from_filename('Model/'+modelpath+'/variables/'+i)
        for i in os.listdir('Model/'+modelpath+'/assets'):
            blob = bucket.blob(dir_name+'/'+model_name +
                               '/'+modelpath+'/assets/'+i)
            blob.upload_from_filename('Model/'+modelpath+'/assets/'+i)

        # with open(param.data_dir) as f:
        #     data = json.load(f)
        data = json.loads(param.data_dir)
        publisher = pubsub.PublisherClient()
        topic_path = publisher.topic_path(
            data['project_name'], data['topic_name'])

        dic = {
            'gcppid': data['gcppid'],
            'gcsb': bucket_name,
            'gcsdir': dir_name,
            'dport': data['restport'],
            'modelname': model_name,
            'modelpath': dir_name,
            'labellerrpid': data['labellerrpid'],
            'quesid': data['quesid'],
            'region': data['region'],
            'image_path': data['image_path']
        }
        data = str(json.dumps(dic))
        future = publisher.publish(topic_path, data=data.encode("utf-8"))


def make_params_global(params):
    '''Function to make command line arguments parameters global

        Parameters:
            params      - The local parameters variable to be converted to global scope
        Return Value:
            None
    '''

    global param
    param = params


def train_model(params):
    '''Function to train the model and upload the model on GCP GCS Bukcet.

        Parameters:
            params      - The parameters required to fetch the data and train the model
        Return Value:
            None
    '''
    make_params_global(params)
    train_data, val_data, train_size, val_size, num_classes = data_factory.read_data(
        params, 224)

    batch_size = int(train_size/params.steps_per_epoch)
    val_steps = int(val_size/batch_size)

    t_ds = train_data.batch(batch_size, drop_remainder=True)
    t_ds = t_ds.prefetch(buffer_size=int(params.steps_per_epoch/2))

    v_ds = val_data.batch(batch_size, drop_remainder=True)
    v_ds = v_ds.prefetch(buffer_size=int(val_steps/2))

    model_architect = InceptionV3Model((224, 224, 3), num_classes)
    model = model_architect.get_model()

    e_s = EarlyStopping(monitor='val_binary_accuracy',
                        mode='max', verbose=1, patience=5)
    m_c = ModelCheckpoint("Model/{epoch:02d}", monitor='val_binary_accuracy',
                            mode='max', save_best_only=True, verbose=1)

    lcb = LambdaCallback(on_epoch_end=epoch_end)

    class MyCustomCallback(tf.keras.callbacks.Callback):
        '''Class to return custom callback while training model.

            Parameters:
                tf.keras.callbacks.Callback - Abstract base class used to build new callbacks.
        '''

        def on_epoch_end(self, epoch, logs=None):
            '''Function to collect garbage after each epoch.

                Parameters:
                    epoch   - Training epoch number
                    logs    - Log verbose to be monitored
            '''
            gc.collect()

    model.fit(t_ds, validation_data=v_ds, epochs=params.epochs,
                steps_per_epoch=params.steps_per_epoch,
                verbose=1, validation_steps=val_steps,
                callbacks=[MyCustomCallback(), e_s, m_c, lcb])


def _get_params_from_flags(flags_obj):
    '''Function to get parameters dictionary from flags

        Parameters:
            flags_obj   - The parameters passed during calling train script.
        Return Value:
            None
    '''

    flags_overrides = {
        'model_dir': flags_obj.model_dir,
        'data_dir': flags_obj.data_dir,
        'run_eagerly': flags_obj.run_eagerly,
        'resize_function': flags_obj.resize_function,
        'repeat': flags_obj.repeat,
        'multi_worker': flags_obj.multi_worker,
        'epochs': flags_obj.epochs,
        'steps_per_epoch': flags_obj.steps_per_epoch
    }
    params = namedtuple('Struct', flags_overrides.keys()
                        )(*flags_overrides.values())
    return params


def define_classifier_flags():
    '''Function defines common flags for image classification

        Parameters:
            None
        Return Value:
            None
    '''

    flags.DEFINE_string(
        'data_dir',
        default=None,
        help='The location of the input data.')
    flags.DEFINE_string(
        'model_dir',
        default=None,
        help='The location to save the model')
    flags.DEFINE_bool(
        'run_eagerly',
        default=False,
        help='Use eager execution and disable autograph for debugging.')
    flags.DEFINE_string(
        'resize_function',
        default='nearest',
        help='Image resize function. Other Functions are: bilinear, lanczos3, lanczos5, bicubic, gaussian, nearest, area, mitchellcubic')
    flags.DEFINE_bool(
        'repeat',
        default=False,
        help='Repeat the dataset. In case of small dataset where batch size becomes less than 1, it will automatically be repeated and that cannot be overridden.')
    flags.DEFINE_bool(
        'multi_worker',
        default=False,
        help='Enable multi-worker strategy')
    flags.DEFINE_integer(
        'epochs',
        default=None,
        help='The number of epochs for which the model needs to be trained')
    flags.DEFINE_integer(
        'steps_per_epoch',
        default=None,
        help='The number of batches per epoch for which the model needs to be trained')


def run(flags_obj):
    '''Function to run the train job.

        Parameters:
            flags_obj   - The parameters passed during calling train script.
        Return Value:
            None
    '''

    params = _get_params_from_flags(flags_obj)
    train_model(params)


def main(_):
    '''Main Function.

        Parameters:
            flags_obj   - The parameters passed during calling train script.
        Return Value:
            None
    '''

    run(flags.FLAGS)


if __name__ == '__main__':
    logging.set_verbosity(logging.INFO)
    define_classifier_flags()
    flags.mark_flag_as_required('data_dir')
    flags.mark_flag_as_required('model_dir')

    app.run(main)
