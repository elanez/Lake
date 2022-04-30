import traci
import numpy as np
import os
import sys
import logging

from routing import Routing

'''
Logger
'''
logger = logging.getLogger('test_logs')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('test.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

'''
INITIALIZE
'''
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    error_message = "please declare environment variable 'SUMO_HOME'"
    sys.exit(error_message)

sumo = ["sumo", "-c", "sumo_files/sumo_config.sumocfg"]
sumo_intersection = Routing(1000, 3600) #(number of cars, max steps))
max_step = 3600

'''
FUNCTIONS
'''
def run(episode):
    sumo_intersection.generate_routefile(episode)
    traci.start(sumo)

    # traffic_light = traci.trafficlight.getIDList
    # lanes = traci.trafficlight.getControlledLanes
    # logger.info(f'TrafficLightID: {traffic_light}, Lanes: {lanes}')

    for _ in range(max_step):
        # logger.info(get_state())
        get_state()
        traci.simulationStep()
    
    traci.close()

def get_state():
    traffic_light_list = traci.trafficlight.getIDList()
    lanes = traci.trafficlight.getControlledLanes(traffic_light_list[0])

    #remove duplicate
    temp_list = []
    for i in lanes:
        if i not in temp_list:
            temp_list.append(i)
    lanes = temp_list

    # logger.info(f'Lanes: {lanes}')
    state = np.zeros(len(lanes))
    state_i = 0
    car_count = 0
    
    for index, l in enumerate(lanes):
        car_count = traci.lane.getLastStepVehicleNumber(l)
        # logger.info(f'Lane: {l}, Car Count:{car_count}')
        # logger.info(f'index: {index}, lane:{l}')
        state[state_i] = car_count
        state_i += 1

    # logger.info(f'TrafficLightID: {traffic_light_list}, Lanes: {lanes}')               
    return state

'''
Simulation
'''
episodes = 1

for i in range(episodes):
    run(i)