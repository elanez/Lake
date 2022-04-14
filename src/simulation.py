import os
import sys
import numpy as np
import random
import traci

from routing import Routing
from sumolib import checkBinary

class Simulation:
    def __init__(self):
        self._sumo_cmd = self._set_sumo(False, 'sumo_config.sumocfg')
        self._sumo_intersection = Routing(1000, 60)
        self._num_states = 100
        # self._gamma
        # self._actions
        # self._epochs

    def run(self):
        '''
        Run simulation
        '''
        print('Starting simulation...')

        self._sumo_intersection.generate_routefile(42)
        traci.start(self._sumo_cmd)
        traci.close()
        print('Simulation - DONE')
    
    def _get_state(self):
        state = np.zeros(self._num_states)
        car_list = traci.vehicle.getIDList()

    '''
    UTILS
    '''
    def _set_sumo(self, gui, sumocfg_filename):
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            sys.exit("please declare environment variable 'SUMO_HOME'")
        
        if gui == True:
            sumoBinary = checkBinary('sumo-gui')
        else:
            sumoBinary = checkBinary('sumo')

        return [sumoBinary, "-c", os.path.join('sumo_files', sumocfg_filename)]