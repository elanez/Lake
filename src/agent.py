import os
import sys
import random
import numpy as np

from tensorflow import keras
from tensorflow.keras.optimizers import Adam
from keras import layers, losses
from keras.models import load_model

class Agent:
    def __init__(self):
        self.input_dim = 3
        self.output_dim = 2
        self.batch_size = 100
        self.learning_rate = 0.1
        self._model = self._create_model(4, 400)
        self.samples = []
        self.size_max = 50000
        self.size_min = 600

    '''
    INITIALIZE MODEL
    '''
    
    def _create_model(self, num_layers, width):
        inputs = keras.Input(shape=(self.input_dim,))
        x = layers.Dense(width, activation='relu')(inputs)
        for _ in range(num_layers):
            x = layers.Dense(width, activation='relu')(x)
        outputs = layers.Dense(self.output_dim, activation='linear')(x)

        model = keras.Model(inputs=inputs, outputs=outputs, name='model')
        model.compile(loss=losses.mean_squared_error, optimizer=Adam(lr=self.learning_rate))

        #test
        model.summary()

        return model
    
    def _load_model(self, file_name):
        #file_location = f'.../models/{file_name}.h5'
        model_file_path = os.path(f'.../models/{file_name}.h5')
        
        if os.path.isfile(model_file_path):
            loaded_model = load_model(model_file_path)
            return loaded_model
        else:
            sys.exit("Model not found")
    
    '''
    TRAINING ARC
    '''
    def predict_one(self, state):
        state = np.reshape(state, [1, self._input_dim])
        return self._model.predict(state)

    def predict_batch(self, states):
        return self._model.predict(states)

    def train_batch(self, states, q):
        self._model.fit(states, q, epochs=1, verbose=0)

    def save_model(self, file_name):
        #file_location = f'.../models/{file_name}.h5'
        self._model.save(os.path(f'.../models/{file_name}.h5'))
    
    '''
    EXPRIENCE REPLAY / MEMORY
    '''

    def add_sample(self, sample):
        self.samples.append(sample)
        if self._size_now() > self.size_max:
            self.samples.pop(0) 

    def get_samples(self, n):
        if self._size_now() < self.size_min:
            return []

        if n > self._size_now():
            return random.sample(self.samples, self._size_now())  
        else:
            return random.sample(self.samples, n)

    def _size_now(self):
        return len(self.samples)