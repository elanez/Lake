import os
import sys
import random
import numpy as np
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras.optimizers import Adam
from keras import layers, losses
from keras.models import load_model
from logger import getLogger

class Agent:
    def __init__(self):
        self._input_dim = 80
        self._output_dim = 2
        self._batch_size = 100
        self._learning_rate = 0.1
        self._model = self._create_model(4, 400) #(number of layers, width)

        #MEMORY
        self.samples = []
        self.size_max = 50000
        self.size_min = 600

    '''
    INITIALIZE MODEL
    '''
    def _create_model(self, num_layers, width): #CONSTRUCT NEURAL NET
        getLogger().info('Create model...')

        #Look for gpu
        if tf.test.gpu_device_name():
            getLogger().info('==== Default GPU Device: {} ==='.format(tf.test.gpu_device_name()))
        else:
            getLogger().warning('=== Please install GPU version of Tf ===')

        inputs = keras.Input(shape=(self._input_dim,))
        x = layers.Dense(width, activation='relu')(inputs)
        for _ in range(num_layers):
            x = layers.Dense(width, activation='relu')(x)
        outputs = layers.Dense(self._output_dim, activation='linear')(x)

        model = keras.Model(inputs=inputs, outputs=outputs, name='model')
        model.compile(loss=losses.mean_squared_error, optimizer=Adam(lr=self._learning_rate))

        #test
        #model.summary()
        getLogger().info('Create Model - DONE')

        return model
    
    def _load_model(self, file_name): #LOAD MODEL FILE
        #file_location = f'.../models/{file_name}.h5'
        getLogger().info('Load Model...')
        model_file_path = os.path(f'.../models/{file_name}.h5')
        
        if os.path.isfile(model_file_path):
            loaded_model = load_model(model_file_path)
            getLogger().info('Load Model - DONE')
            return loaded_model
        else:
            error_message = 'Model not found!'
            getLogger().critical(error_message)
            sys.exit(error_message)
    
    '''
    TRAINING ARC
    '''
    def predict_one(self, state): #PREDICT ACTION: SINGLE STATE
        state = np.reshape(state, [1, self._input_dim])
        return self._model.predict(state)

    def predict_batch(self, states): #PREDICT ACTION: BATCH OF STATES
        return self._model.predict(states)

    def train_batch(self, states, q): #TRAIN NEURAL NET
        self._model.fit(states, q, epochs=1, verbose=0)

    def save_model(self, file_name): #SAVE MDOEL TO "models" FOLDER
        self._model.save(os.path(f'.../models/{file_name}.h5'))
    
    '''
    EXPRIENCE REPLAY / MEMORY
    '''
    def add_sample(self, sample): #ADD TO MEMORY
        self.samples.append(sample)
        if self._size_now() > self.size_max:
            self.samples.pop(0) 

    def get_samples(self, n): #GET n RANDOM FROM MEMORY
        if self._size_now() < self.size_min:
            return []

        if n > self._size_now():
            return random.sample(self.samples, self._size_now())  
        else:
            return random.sample(self.samples, n)

    def _size_now(self): #GET MEMORY LENGTH
        return len(self.samples)