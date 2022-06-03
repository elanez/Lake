import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2' #remove tensorflow warning

import sys
import random
import numpy as np
import tensorflow as tf

from plot import Plot
from collections import deque
from tensorflow import keras
from tensorflow.keras.optimizers import Adam
from keras import losses
from keras.layers import Input, Flatten, Dense, concatenate
from keras.models import load_model
from logger import getLogger

class Agent:
    def __init__(self, config, output_dim, num_lanes):
        self._input_dim = config['input_dim']
        self._output_dim = output_dim
        self._num_layers = config['num_layers']
        self._batch_size = config['batch_size']
        self._learning_rate = config['learning_rate']
        self.num_lanes = num_lanes
        self.id = f'model_{self._input_dim}.{self.num_lanes}.{self._output_dim}'

        #MEMORY
        self._size_min = config['size_min']
        self.samples = deque(maxlen=config['size_max'])

        self._model = self._create_model(self._input_dim , self._num_layers)
        
    '''
    INITIALIZE MODEL
    '''
    def _create_model(self, input_dim, num_layers): #CONSTRUCT NEURAL NET
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

        input_dim = ((2 * (self.num_lanes * input_dim)) + 4)
        hidden_dim = int((2 * input_dim) / 3)

        x = concatenate([x1, x2, input_3])

        for _ in range(num_layers):
            x = Dense(hidden_dim, activation='relu')(x)

        outputs = Dense(self._output_dim, activation='linear')(x)

        model = keras.Model(inputs=[input_1, input_2, input_3], outputs=outputs, name='model')
        model.compile(loss=losses.mean_squared_error,
        optimizer=Adam(learning_rate=self._learning_rate),
        metrics=['accuracy'])

        # model.summary()
        getLogger().info(f'Model Parameter: ID: {self.id} input_dim: {input_dim} hidden_dim: {hidden_dim} output_dim: {self._output_dim}')
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
        self._model.fit(self.get_input_state(states), q, epochs=1, verbose=0)

    def save_model(self, path): #SAVE MDOEL
        path = os.path.join(path, f'{self.id}.h5')
        self._model.save(path)
        getLogger().info(f'Saved model to {path}')
    
    def plot_data(self, path, dpi, tl):
        plot = Plot(path, dpi)
        plot.plot_data(data=tl.reward_store, filename='reward', xlabel='Episode', ylabel='Cumulative reward')
        plot.plot_data(data=tl.cumulative_wait_store, filename='delay', xlabel='Episode', ylabel='Cumulative delay (s)')
        plot.plot_data(data=tl.avg_queue_length_store, filename='queue', xlabel='Episode', ylabel='Average queue length (vehicles)')
    
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

    def get_samples(self, n): #GET n RANDOM FROM MEMORY
        if self._size_now() < self._size_min:
            return []

        if n > self._size_now():
            return random.sample(self.samples, self._size_now())  
        else:
            return random.sample(self.samples, n)

    def _size_now(self): #GET MEMORY LENGTH
        return len(self.samples)
    
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
    def __init__(self, id, input_dim, num_lanes, model_path):
        self.id = id
        self._input_dim = input_dim
        self.num_lanes = num_lanes
        self._model = self._load_model(model_path)
    
    def _load_model(self, path): #LOAD MODEL FILE
        getLogger().info('Load Model...')
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