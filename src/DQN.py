import os
import sys
import random
import numpy as np

from tensorflow import keras
from keras import layers, losses
from keras.models import load_model
from keras.optimizers import Adam

class DQN:
    def __init__(self):
        self.input_dim
        self.output_dim
        self.batch_size
        self.learning_rate
        self._model = self._build_model()
        self.sample
        self.size_max
        self.size_min

    def _create_model(self, num_layers, width):
        #Create a fully connected neural network
        inputs = keras.Input(shape=(self._input_dim,))
        x = layers.Dense(width, activation='relu')(inputs)
        for _ in range(num_layers):
            x = layers.Dense(width, activation='relu')(x)
        outputs = layers.Dense(self._output_dim, activation='linear')(x)

        model = keras.Model(inputs=inputs, outputs=outputs, name='my_model')
        model.compile(loss=losses.mean_squared_error, optimizer=Adam(lr=self._learning_rate))
        return model

    def save_model(self):
        self._model.save(os.path('../Models/trained_model.h5'))
    
    def _load_model(self):
        model_file_path = os.path('../Models/trained_model.h5')
        
        if os.path.isfile(model_file_path):
            loaded_model = load_model(model_file_path)
            return loaded_model
        else:
            sys.exit("Model not found")

    #EXPRIENCE REPLAY
    def add_sample(self, sample):
        self._samples.append(sample)
        if self._size_now() > self._size_max:
            self._samples.pop(0) 

    def get_samples(self, n):
        if self._size_now() < self._size_min:
            return []

        if n > self._size_now():
            return random.sample(self._samples, self._size_now())  
        else:
            return random.sample(self._samples, n)

    def _size_now(self):
        return len(self._samples)