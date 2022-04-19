import os
import sys
import numpy as np
import random
import traci

from logger import getLogger
from routing import Routing
from sumolib import checkBinary

#PHASE CODE from SUMO
PHASE_EW_GREEN = 0
PHASE_EW_YELLOW = 1
PHASE_EWS_GREEN = 2
PHASE_EWS_YELLOW = 3
PHASE_NS_GREEN = 4
PHASE_NS_YELLOW = 5
PHASE_NSS_GREEN = 6
PHASE_NSs_YELLOW = 7

class Simulation:
    def __init__(self):
        self._sumo_cmd = self._set_sumo(False, 'sumo_config.sumocfg') #(gui, filename)
        self._sumo_intersection = Routing(1000, 60) #(number of cars, max steps)
        self._num_states = 100
        self._episodes = 50
        # self._gamma
        # self._actions
        # self._epochs

    '''
    SUMO INTERACTIONS
    '''
    def run(self): #RUN SIMULATION
        getLogger().info('Starting simulation...')

        self._sumo_intersection.generate_routefile(self._episodes)
        traci.start(self._sumo_cmd)

        traci.close()
        getLogger().info('Simulation - DONE')
    
    def _get_state(self): #GET STATE FROM SUMO
        state = np.zeros(self._num_states)
        car_list = traci.vehicle.getIDList()
    
    def _choose_action(self, state, epsilon): #CHOOSE ACTION
        if random.random() < epsilon:
            return random.randint(0, self._num_actions - 1) #explore
        else:
            return np.argmax(self._Model.predict_one(state)) #exploit

    '''
    UTILS
    '''
    def _set_sumo(self, gui, sumocfg_filename): #CONFIGURE SUMO
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
    
    def _get_waiting_time(self): #GET ALL WAITING TIME FOR ALL INCOMING LANES
        incoming_roads = ["top_in", "right_in", "left_in", "bottom_in"]
        car_list = traci.vehicle.getIDList()

        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)
            if road_id in incoming_roads:
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times: #if car has left the intersection
                    del self._waiting_times[car_id]
        
        total_waiting_time = sum(self._waiting_times.values())
        return total_waiting_time
    
    def _get_queue_length(self): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        road_N = traci.edge.getLastStepHaltingNumber("top_in")
        road_E = traci.edge.getLastStepHaltingNumber("right_in")
        road_S = traci.edge.getLastStepHaltingNumber("bottom_in")
        road_W = traci.edge.getLastStepHaltingNumber("left_in")
        
        queue_length = road_N + road_E + road_S + road_W
        return queue_length