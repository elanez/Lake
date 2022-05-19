import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2' #remove tensorflow warning

import sys
import random
import numpy as np
import tensorflow as tf

from collections import deque
from tensorflow import keras
from tensorflow.keras.optimizers import Adam
from keras import losses
from keras.layers import Input, Flatten, Dense, concatenate
from keras.models import load_model
from logger import getLogger

class Agent:
    def __init__(self, input_dim, output_dim, batch_size, learning_rate, num_lanes, size_min, size_max):
        self._input_dim = input_dim
        self._output_dim = output_dim
        self._batch_size = batch_size
        self._learning_rate = learning_rate
        self.num_lanes = num_lanes
        self._model = self._create_model(self._input_dim) 

        #MEMORY
        self._size_min = size_min
        # self._size_max = size_max
        self.samples = deque(maxlen=size_max)

        #DATA
        self._loss_history = []
        self._acc_history = []
        self._epochs = 0
        
    '''
    INITIALIZE MODEL
    '''
    def _create_model(self, input_dim): #CONSTRUCT NEURAL NET
        getLogger().info('Create model...')

        #Look for gpu
        if tf.test.gpu_device_name():
            getLogger().info(f'==== Default GPU Device: {tf.test.gpu_device_name()} ===')
        else:
            getLogger().warning('=== Please install GPU version of Tf ===')

        input_1 = Input(shape=(self.num_lanes, input_dim,)) #position
        x1 = Flatten()(input_1)

        input_2 = Input(shape=(self.num_lanes, input_dim,)) #velocity
        x2 = Flatten()(input_2)

        input_3 = Input(shape=(4,))    #traffic light phase

        x = concatenate([x1, x2, input_3])
        x = Dense(128, activation='relu')(x)
        x = Dense(64, activation='relu')(x)

        outputs = Dense(self._output_dim, activation='linear')(x)

        model = keras.Model(inputs=[input_1, input_2, input_3], outputs=outputs, name='model')
        model.compile(loss=losses.mean_squared_error,
        optimizer=Adam(learning_rate=self._learning_rate),
        metrics=['accuracy'])

        #test
        # model.summary()
        getLogger().info('Create Model - DONE')

        return model
    
    '''
    TRAINING ARC
    '''
    def predict_one(self, state): #PREDICT ACTION: SINGLE STATE  
        input_1 = np.reshape(state[0], (1, self.num_lanes, self._input_dim, 1))
        input_2 = np.reshape(state[1], (1, self.num_lanes, self._input_dim, 1))
        input_3 = np.reshape(state[2], (1, 4, 1))

        return self._model.predict([input_1, input_2, input_3])

    def predict_batch(self, states): #PREDICT ACTION: BATCH OF STATES
        return self._model.predict(self.get_input_state(states))

    def train_batch(self, states, q): #TRAIN NEURAL NET
        history = self._model.fit(self.get_input_state(states), q, epochs=1, verbose=0)
        self._loss_history.append(history.history['loss'])
        self._acc_history.append(history.history['accuracy'])
        self._epochs = self._epochs + 1

    def save_model(self, path): #SAVE MDOEL
        path = os.path.join(path, 'model.h5')
        self._model.save(path)
        getLogger().info(f'Saved model to {path}')
    
    def get_input_state(self, states):
        input_1 = np.array([val[0] for val in states])
        input_2 = np.array([val[1] for val in states])
        input_3 = np.array([val[2] for val in states])
        return [input_1, input_2, input_3]
    
    '''
    EXPRIENCE REPLAY / MEMORY
    '''
    def add_sample(self, sample): #ADD TO MEMORY
        self.samples.append(sample)
        # if self._size_now() > self.size_max:
        #     self.samples.pop(0) 

    def get_samples(self, n): #GET n RANDOM FROM MEMORY
        if self._size_now() < self._size_min:
            return []

        if n > self._size_now():
            return random.sample(self.samples, self._size_now())  
        else:
            return random.sample(self.samples, n)

    def _size_now(self): #GET MEMORY LENGTH
        return len(self.samples)
    
    '''
    DATA RESET
    '''
    def reset_data(self):
        self._loss_history.clear()
        self._acc_history.clear()
        self._epochs = 0

    @property
    def loss_history(self):
        return self._loss_history

    @property
    def acc_history(self):
        return self._acc_history
    

'''
LOAD AND TEST AGENT
'''
class TestAgent():
    def __init__(self,input_dim, num_lanes, model_path):
        self._input_dim = input_dim
        self.num_lanes = num_lanes
        self._model = self._load_model(model_path)
    
    def _load_model(self, path): #LOAD MODEL FILE
        getLogger().info('Load Model...')

        path = os.path.join(path, 'model.h5')
        getLogger().info(f'Model at: {path}')
        
        if os.path.isfile(path):
            loaded_model = load_model(path)
            getLogger().info('Load Model - DONE')
            return loaded_model
        else:
            error_message = 'Model not found!'
            getLogger().critical(error_message)
            sys.exit(error_message)

    def predict_one(self, state): #PREDICT ACTION: SINGLE STATE  
        input_1 = np.reshape(state[0], (1, self.num_lanes, self._input_dim, 1))
        input_2 = np.reshape(state[1], (1, self.num_lanes, self._input_dim, 1))
        input_3 = np.reshape(state[2], (1, 4, 1))

        return self._model.predict([input_1, input_2, input_3])