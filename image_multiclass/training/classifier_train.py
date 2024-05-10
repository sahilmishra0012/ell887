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
from models import InceptionV3Model
import data_factory
from db_client import CloudSQLDB

warnings.filterwarnings("ignore")

global best_categorical_accuracy
best_categorical_accuracy = -10

DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_NAME = os.environ["DB_NAME"]
global connect
db = CloudSQLDB(user=DB_USER, password=DB_PASS, db=DB_NAME)
connect = db.create_connection()

def epoch_end(epoch, logs):
    '''Function to save and upload model to GCS bucket and send Pub/Sub messages on ModelCheckpoint.
        Parameters:
            epoch   - The epoch while training the model
            logs    - The logs of metrics and losses during training
        Return Value:
            None
    '''

    storage_client = storage.Client()

    global best_categorical_accuracy

    splits = param.model_dir.split('/')

    bucket_name = splits[2]
    dir_name = ""
    for i in splits[3:-1]:
        dir_name = dir_name+"/"+i
    dir_name = dir_name[1:]
    model_name = splits[-1]

    # with open(param.data_dir) as f:
    #     data = json.load(f)
    data = json.loads(param.data_dir)

    if best_categorical_accuracy < logs['val_categorical_accuracy']:
        best_categorical_accuracy = logs['val_categorical_accuracy']
        modelpath = sorted(os.listdir('Model'))[-1]
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(dir_name+'/'+model_name+'/' +
                           modelpath+'/saved_model.pb')
        blob.upload_from_filename('Model/'+modelpath+'/pytorch_model.bin')
        for i in os.listdir('Model/'+modelpath+'/variables'):
            blob = bucket.blob(dir_name+'/'+model_name +
                               '/'+modelpath+'/variables/'+i)
            blob.upload_from_filename('Model/'+modelpath+'/variables/'+i)
        for i in os.listdir('Model/'+modelpath+'/assets'):
            blob = bucket.blob(dir_name+'/'+model_name +
                               '/'+modelpath+'/assets/'+i)
            blob.upload_from_filename('Model/'+modelpath+'/assets/'+i)

        publisher = pubsub.PublisherClient()
        topic_path = publisher.topic_path('autolabel-287715', 'deploy')

        dic = {
            'gcsb': bucket_name,
            'gcsdir': dir_name,
            'modelname': model_name,
            'modelpath': modelpath,
            'project_id': data['project_id'],
            'quesid': data['question']['question_id'],
            'image_path': data['image_path'],
            'model_id' : data['model_id'],
            'model_algorithm_id' : data['model_algorithm_id'],
            'loss' : logs['loss'],
            'val_loss' : logs['val_loss'],
            'metric' : logs['categorical_accuracy'],
            'val_metric' : logs['val_categorical_accuracy'],
            'data_type': 'image',
            'model_type': 'multiclass classification'
        }
        pub_sub_data = str(json.dumps(dic))
        future = publisher.publish(topic_path, data=pub_sub_data.encode("utf-8"))
    db.write_logs(connect, data['model_id'], "In Progress", logs, data['job_id'])


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
        params, params.model_shape)

    # with open(param.data_dir) as f:
    #     data = json.load(f)
    data = json.loads(param.data_dir)

    batch_size = int(train_size/params.steps_per_epoch)
    try:
        val_steps = int(val_size/batch_size)
    except:
        val_steps = params.steps_per_epoch

    t_ds = train_data.batch(batch_size, drop_remainder=True)
    t_ds = t_ds.prefetch(buffer_size=int(params.steps_per_epoch/2))

    v_ds = val_data.batch(batch_size, drop_remainder=True)
    v_ds = v_ds.prefetch(buffer_size=int(val_steps/2))

    model_architect = InceptionV3Model(
        (params.model_shape, params.model_shape, 3), num_classes)
    model = model_architect.get_model()

    e_s = EarlyStopping(monitor='val_categorical_accuracy',
                        mode='max', verbose=1, patience=5)
    m_c = ModelCheckpoint("Model/{epoch:02d}", monitor='val_categorical_accuracy',
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
    try:

        db.write_logs(connect, data['model_id'], "Start", "Training Started", data['job_id'])

        model.fit(t_ds, validation_data=v_ds, epochs=params.epochs,
                    steps_per_epoch=params.steps_per_epoch,
                    verbose=1, validation_steps=val_steps,
                    callbacks=[MyCustomCallback(), e_s, m_c, lcb])
        db.write_logs(connect, data['model_id'], "Stop", "Training Completed", data['job_id'])

    except Exception as err:
        db.write_logs(connect, data['model_id'], "stop", "Error Occured:\n"+str(err), data['job_id'])
    db.disconnect(connect)


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
        'steps_per_epoch': flags_obj.steps_per_epoch,
        'model_shape': flags_obj.model_shape
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
        default=300,
        help='The number of epochs for which the model needs to be trained')
    flags.DEFINE_integer(
        'steps_per_epoch',
        default=128,
        help='The number of batches per epoch for which the model needs to be trained')
    flags.DEFINE_integer(
        'model_shape',
        default=224,
        help='The shape of Input Layer of the model')


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
