import os
import sys
import configparser

from logger import getLogger
from sumolib import checkBinary

def import_train_config(file): #CONFIGURE SETTINGS FOR TRAINING
    content = configparser.ConfigParser()
    content.read(file)
    config = {}

    #Agent
    config['input_dim'] = content['agent'].getint('input_dim')
    config['num_layers'] = content['agent'].getint('num_layers')
    config['batch_size'] = content['agent'].getint('batch_size')
    config['learning_rate'] = content['agent'].getfloat('learning_rate')

    #memory
    config['size_max'] = content['memory'].getint('size_max')
    config['size_min'] = content['memory'].getint('size_min')

    #simulation
    config['total_episodes'] = content['simulation'].getint('total_episodes')
    config['sumo_gui'] = content['simulation'].getboolean('sumo_gui')
    config['max_step'] = content['simulation'].getint('max_step')
    config['num_lanes'] = content['simulation'].getint('num_lanes')
    config['epochs'] = content['simulation'].getint('epochs')
    config['gamma'] = content['simulation'].getfloat('gamma')
    config['green_duration'] = content['simulation'].getint('green_duration')
    config['yellow_duration'] = content['simulation'].getint('yellow_duration')

    #routing
    config['num_cars'] = content['routing'].getint('num_cars')

    #dir
    config['sumocfg_file'] = content['dir']['sumocfg_file']
    config['model_folder'] = content['dir']['model_folder']

    return config

def import_test_config(file): #CONFIGURE SETTINGS FOR TESTING
    content = configparser.ConfigParser()
    content.read(file)
    config = {}

    #agent
    config['input_dim'] = content['agent'].getint('input_dim')

    #simulation
    config['episode_seed'] = content['simulation'].getint('episode_seed')
    config['sumo_gui'] = content['simulation'].getboolean('sumo_gui')
    config['max_step'] = content['simulation'].getint('max_step')
    config['num_lanes'] = content['simulation'].getint('num_lanes')
    config['green_duration'] = content['simulation'].getint('green_duration')
    config['yellow_duration'] = content['simulation'].getint('yellow_duration')

    #routing
    # config['num_cars'] = content['routing'].getint('num_cars')

    #dir
    config['sumocfg_file'] = content['dir']['sumocfg_file']
    config['model_folder'] = content['dir']['model_folder']

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

def set_model_path(path_name): #CONFIGURE MODEL PATH AND INCREMENT FILE NAME
    model_path = os.path.join(os.getcwd(), 'models')

    if not os.path.exists(model_path):
        os.makedirs(model_path)
        getLogger().info('Created a new directory at {model_path}')

    model_path = os.path.join(model_path, path_name)

    counter = 1

    while os.path.exists(model_path): #If file name already exists add a number eg folder_name (1)
        if "(" in model_path and ")" in model_path:
            model_path = model_path.replace(str(counter-1), str(counter))
        else:
            model_path = model_path + " (" + str(counter) + ")"
        counter += 1
    
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    return model_path

def get_model_path(path_name):
    model_path = os.path.join(os.getcwd(),'models', path_name)

    if os.path.isdir(model_path):
        plot_path = os.path.join(model_path, 'test_data')
        os.makedirs(plot_path, exist_ok=True)
        return model_path, plot_path
    else: 
        msg = 'Folder does not exist'
        getLogger().critical(msg)
        sys.exit(msg)
