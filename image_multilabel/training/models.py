"Script to load models for Multi-Label Image Classification"

from __future__ import absolute_import, division, print_function
import tensorflow as tf
from tensorflow.keras import regularizers
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.optimizers import Adam, SGD
from absl import logging


class InceptionV3Model:
    '''Class to create InceptionV3 Model object.

            Parameters:
                input_shape     - Shape of the Input Layer.
                output_shape	- Number of classes to be given as output.
    '''

    def __init__(self, input_shape, output_shape):
        self.input_shape = input_shape
        self.output_shape = output_shape
        self.name = 'InceptionV3'

    def get_model(self):
        '''Function to load InceptionV3 Model.

            Parameters:
                input_shape     - Shape of the Input Layer.
                output_shape	- Number of classes to be given as output.
            Return Value:
                Tensorflow Keras InceptionV3 Model.
        '''
        
        def macro_f1(y, y_hat, thresh=0.5):
                """Compute the macro F1-score on a batch of observations (average F1 across labels)

            Args:
                y (int32 Tensor): labels array of shape (BATCH_SIZE, N_LABELS)
                y_hat (float32 Tensor): probability matrix from forward propagation of shape (BATCH_SIZE, N_LABELS)
                thresh: probability value above which we predict positive

            Returns:
                macro_f1 (scalar Tensor): value of macro F1 for the batch
            """
            y_pred = tf.cast(tf.greater(y_hat, thresh), tf.float32)
            tp = tf.cast(tf.math.count_nonzero(y_pred * y, axis=0), tf.float32)
            fp = tf.cast(tf.math.count_nonzero(y_pred * (1 - y), axis=0), tf.float32)
            fn = tf.cast(tf.math.count_nonzero((1 - y_pred) * y, axis=0), tf.float32)
            f1 = 2*tp / (2*tp + fn + fp + 1e-16)
            macro_f1 = tf.reduce_mean(f1)
            return macro_f1


        def macro_soft_f1(y, y_hat):
            """Compute the macro soft F1-score as a cost (average 1 - soft-F1 across all labels).
            Use probability values instead of binary predictions.

            Args:
                y (int32 Tensor): targets array of shape (BATCH_SIZE, N_LABELS)
                y_hat (float32 Tensor): probability matrix from forward propagation of shape (BATCH_SIZE, N_LABELS)

            Returns:
                cost (scalar Tensor): value of the cost function for the batch
            """
            y = tf.cast(y, tf.float32)
            y_hat = tf.cast(y_hat, tf.float32)
            tp = tf.reduce_sum(y_hat * y, axis=0)
            fp = tf.reduce_sum(y_hat * (1 - y), axis=0)
            fn = tf.reduce_sum((1 - y_hat) * y, axis=0)
            soft_f1 = 2*tp / (2*tp + fn + fp + 1e-16)
            cost = 1 - soft_f1  # reduce 1 - soft-f1 in order to increase soft-f1
            macro_cost = tf.reduce_mean(cost)  # average on all labels
            return macro_cost

        inception = InceptionV3(
            weights='imagenet', include_top=False, input_shape=self.input_shape)
        for layer in inception.layers:
            layer.trainable = False
        x_layer = inception.output
        x_layer = GlobalAveragePooling2D()(x_layer)
        x_layer = Dense(128, activation='relu')(x_layer)
        x_layer = Dropout(0.2)(x_layer)

        predictions = Dense(self.output_shape, activation='sigmoid')(x_layer)

        model = Model(inputs=inception.input, outputs=predictions)
        model.compile(optimizer=Adam(lr=0.001),
                      loss=macro_soft_f1, metrics=[macro_f1])
        return model
