import os
import sys
import configparser
import sumolib

from logger import getLogger
from sumolib import checkBinary
from interface.route import Route

def import_train_config(file): #CONFIGURE SETTINGS FOR TRAINING
    content = configparser.ConfigParser()
    content.read(file)
    config = {}

    #Agent
    config['input_dim'] = content['agent'].getint('input_dim')
    config['output_dim'] = content['agent'].getint('output_dim')
    config['num_layers'] = content['agent'].getint('num_layers')
    config['num_lanes'] = content['agent'].getint('num_lanes')
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
    config['green_duration'] = content['simulation'].getint('green_duration')
    config['yellow_duration'] = content['simulation'].getint('yellow_duration')

    #routing
    config['num_cars'] = content['routing'].getint('num_cars')

    #dir
    config['sumo_file'] = content['dir']['sumo_file']
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
    config['green_duration'] = content['simulation'].getint('green_duration')
    config['yellow_duration'] = content['simulation'].getint('yellow_duration')

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
        return [sumoBinary, "-c", os.path.join('sumo_files', f'{sumocfg_filename}.sumocfg')]

def set_path(path_name, folder_name): #Create folder path with incrementing folder name value
    path = os.path.join(path_name, folder_name)
    counter = 1
    while os.path.exists(path): #If file name already exists add a number eg folder_name (1)
        if "(" in path and ")" in path:
            path = path.replace(str(counter-1), str(counter))
        else:
            path = path + " (" + str(counter) + ")"
        counter += 1
    os.makedirs(path, exist_ok=True)
    return path

def get_path(folder_name):
    path = os.path.join(os.getcwd(), folder_name)
    if os.path.exists(path):
        return path
    else:
        msg = 'Path does not exist'
        getLogger().error(msg)
        sys.exit(msg)

def configure_train_settings(net_path):
    net = sumolib.net.readNet(net_path)
    routes = []
    traffic_lights = net.getTrafficLights()

    for tl in traffic_lights:
        tls = net.getTLS(tl.getID())
        # edges = tls.getEdges()
        connections = tls.getConnections()
        for c in connections: #create routes
            edge_in = c[0].getEdge()
            edge_out = c[1].getEdge()
            id = f'{edge_in.getID()}_to_{edge_out.getID()}'
            if not contains(routes, lambda x: x.id == id):
                if edge_in.getFromNode().getCoord()[0] == edge_out.getToNode().getCoord()[0] or edge_in.getFromNode().getCoord()[1] == edge_out.getToNode().getCoord()[1]:
                    type = 'straight'
                else:
                    type = 'turn'
                temp = Route(id , edge_in, edge_out, type)
                routes.append(temp)
        # #get num of lanes
        # num_lanes = 0
        # for e in edges:
        #     num_lanes += e.getLaneNumber()
        # print(f'num_lanes: {num_lanes}')
    return traffic_lights, routes

   
def contains(list, filter):
    for x in list:
        if filter(x):
            return True
    return False

#TEST
# configure_train_settings('sumo_files/1TL/1TL.net.xml')
