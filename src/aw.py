import tensorflow as tf 
#import os; os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
print('tensorflow version', tf.__version__)

 
x = [[3.]]
y = [[4.]]
print('Result: {}'.format(tf.matmul(x, y))) 