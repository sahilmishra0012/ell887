'''
Script to load data from JSON.
'''
import json
import random
import tensorflow as tf
import numpy

def read_jpg(file, shape):

    '''Function to read JPEG Images from GCP GCS bucket.

        Parameters:
            path        - Image files path.
            shape       - Image Shape.
            n_classes   - Number of Classes for OneHot Encoding
        Return Value:
            Processed image and label tensors.
    '''

    image = tf.io.read_file(file)
    image = tf.io.decode_jpeg(image)
    image = tf.image.resize(image, [shape, shape], preserve_aspect_ratio=True, method=param.resize_function)
    s = tf.shape(image)
    paddings = [[0, m-s[i]] for (i, m) in enumerate([shape, shape, 3])]
    image = tf.pad(image, paddings, mode='CONSTANT', constant_values=-1)
    image.set_shape((shape, shape, 3))
    return image


def make_params_global(params):
    '''Function to make command line arguments parameters global

        Parameters:
            params      - The local parameters variable to be converted to global scope
        Return Value:
            None
    '''

    global param
    param = params


def read_data(params, model_shape):

    '''Function to read JSON and return dataset.

        Parameters:
            json_data     - JSON data.
            model_shape   - Image Shape.
        Return Value:
            Processed Tensorflow Dataset.
    '''
    make_params_global(params)
    with open(params.data_dir) as f:
        data = json.load(f)
    # data = json.loads(params.data_dir)

    labels = dict()
    for i, j in enumerate(data['question']['options']):
        labels[j['option_id']] = i

    images = [(a['File URI'], a['labels']) for a in data['records']]

    images1 = []
    for i in images:
        ll = numpy.zeros(len(labels), dtype=numpy.int32)
        for j,k in zip(i[1].index,i[1]):
            ll[labels[j]] = k
        images1.append((i[0], ll.tolist()))

    ll = random.sample(images1, k=len(images))
    images = ll

    train_size = int(len(images) * 0.8)
    val_size = len(images) - train_size
    train_data = images[:train_size]
    val_data = images[train_size:]

    train_files =[]
    train_labels = []
    for i in train_data:
        train_files.append(i[0])
        train_labels.append(i[1])

    val_files = []
    val_labels = []
    for i in val_data:
        val_files.append(i[0])
        val_labels.append(i[1])

    train_files_ds = tf.data.Dataset.from_tensor_slices(train_files)
    train_files_ds = train_files_ds.map(lambda x: read_jpg(x, model_shape))
    train_labels_ds = tf.data.Dataset.from_tensor_slices(train_labels)
    train_img_ds = tf.data.Dataset.zip((train_files_ds, train_labels_ds))


    val_files_ds = tf.data.Dataset.from_tensor_slices(val_files)
    val_files_ds = val_files_ds.map(lambda x: read_jpg(x, model_shape))
    val_labels_ds = tf.data.Dataset.from_tensor_slices(val_labels)
    val_img_ds = tf.data.Dataset.zip((val_files_ds, val_labels_ds))

    return train_img_ds, val_img_ds, train_size, val_size, len(labels)
