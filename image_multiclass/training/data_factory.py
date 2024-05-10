'''
Script to load data from JSON.
'''
import json
import random
import tensorflow as tf

def read_jpg(file, shape, n_classes):

    '''Function to read JPEG Images from GCP GCS bucket.

        Parameters:
            path        - Image files path.
            shape       - Image Shape.
            n_classes   - Number of Classes for OneHot Encoding
        Return Value:
            Processed image and label tensors.
    '''

    image = tf.io.read_file(file[0])
    image = tf.io.decode_png(image, channels = 3)
    image = tf.image.resize(image, [shape, shape], preserve_aspect_ratio=True, method=param.resize_function)
    s = tf.shape(image)
    paddings = [[0, m-s[i]] for (i, m) in enumerate([shape, shape, 3])]
    image = tf.pad(image, paddings, mode='CONSTANT', constant_values=-1)
    image.set_shape((shape, shape, 3))
    out = tf.strings.to_number(file[1])
    out = tf.cast(out, tf.int32)
    ohe = tf.one_hot(out, n_classes)
    return image, ohe


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
    # with open(params.data_dir) as f:
    #     data = json.load(f)
    data = json.loads(params.data_dir)
    labels = dict()
    label_list = []
    for i, j in enumerate(data['question']['options']):
        labels[j['option_id']] = i
        label_list.append((j['option_id'], j['option_name'], i))

    for i in range(len(data['records'])):
        file_name = data['records'][i]['Image ID']+".jpg"
        file_path = tf.keras.utils.get_file(file_name, data['records'][i]['Image SignedURI URI'])
        data['records'][i]['File Path'] = file_path

    images = [(a['File Path'], str(labels[a['Label']])) for a in data['records']]
    ll = random.sample(images, k=len(images))
    images = ll

    train_size = int(len(images) * 0.8)
    val_size = len(images) - train_size
    train_data = images[:train_size]
    val_data = images[train_size:]

    train_img_ds = tf.data.Dataset.from_tensor_slices((train_data))
    train_img_ds = train_img_ds.map(lambda x: read_jpg(x, model_shape, len(list(labels.keys()))))

    val_img_ds = tf.data.Dataset.from_tensor_slices(val_data)
    val_img_ds = val_img_ds.map(lambda x: read_jpg(x, model_shape, len(list(labels.keys()))))

    return train_img_ds, val_img_ds, train_size, val_size, len(list(labels))
