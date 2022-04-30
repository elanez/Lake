import os
import sys
import configparser

from logger import getLogger
from sumolib import checkBinary

def import_configuration(file): #CONFIGURE SETTINGS
    content = configparser.ConfigParser()
    content.read(file)
    config = {}

    #Agent
    config['input_dim'] = content['agent'].getint('input_dim')
    config['output_dim'] = content['agent'].getint('output_dim')
    config['batch_size'] = content['agent'].getint('batch_size')
    config['learning_rate'] = content['agent'].getfloat('learning_rate')

    #memory
    config['size_max'] = content['memory'].getint('size_max')
    config['size_min'] = content['memory'].getint('size_min')

    #simulation
    config['total_episodes'] = content['simulation'].getint('total_episodes')
    config['sumo_gui'] = content['simulation'].getboolean('sumo_gui')
    config['max_step'] = content['simulation'].getint('max_step')
    config['epochs'] = content['simulation'].getint('epochs')
    config['gamma'] = content['simulation'].getfloat('gamma')

    #routing
    config['num_cars'] = content['routing'].getint('num_cars')

    #dir
    config['sumocfg_file'] = content['dir']['sumocfg_file']
    config['model_name'] = content['dir']['model_name']

    return config

def set_sumo(gui, sumocfg_filename): #CONFIGURE SUMO
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            error_message = "please declare environment variable 'SUMO_HOME'"
            getLogger().critical(error_message)
            sys.exit(error_message)
        
        if gui == True:
            sumoBinary = checkBinary('sumo-gui')
        else:
            sumoBinary = checkBinary('sumo')

        return [sumoBinary, "-c", os.path.join('sumo_files', sumocfg_filename)]

def set_model_path(file_name): #CONFIGURE MODEL PATH
    model_path = os.path.join(os.getcwd(), 'models')

    if not os.path.exists(model_path):
        os.makedirs(model_path)

    model_path = os.path.join(model_path, f'{file_name}.h5')

    filename, extension = os.path.splitext(model_path)
    counter = 1

    while os.path.exists(model_path):
        model_path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return model_path
    
set_model_path('model')