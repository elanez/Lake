import os
import sys
import numpy as np
import random
import traci

class Simulation:
    def __init__(self):
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            sys.exit("please declare environment variable 'SUMO_HOME'")

        self._sumo_cmd = ["sumo-gui", "-c", "../sumo_files/environment_config.sumocfg"]
        # self._gamma
        # self._actions
        # self._epochs

    def run(self):
        '''
        Run simulation
        '''
        traci.start(self._sumo_cmd)