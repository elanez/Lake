import os
import sys
import numpy as np
import random
import traci

from routing import Routing

class Simulation:
    def __init__(self):
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            sys.exit("please declare environment variable 'SUMO_HOME'")

        self._sumo_cmd = ["sumo-gui", "-c", "sumo_files/sumo_config.sumocfg"]
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

        print('Simulation - DONE')
    
    def _get_state(self):
        state = np.zeros(self._num_states)
        car_list = traci.vehicle.getIDList()