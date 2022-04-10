import numpy as np
import random
import traci

class Simulation:
    def __init__(self):
        self._sumo_cmd = ["sumo-gui", "-c", "../sumo_files/environment.sumocfg"]
        self._gamma
        self._actions
        self._epochs

    def run(self):
        """
        Run simulation
        """
        traci.start(self._sumo_cmd)