'''
THIS SCRIPT IS USED FOR TESTING
'''

import os
import sys
import numpy as np
import math

sys.path.append(os.path.join(os.getcwd(),'src'))
from logger import getLogger

class Routing:
    def __init__(self, n_cars, max_steps, net_file, routes):
        self._n_cars = n_cars #number of cars per episode
        self._max_steps = max_steps
        self._route_file = os.path.join('sumo_files', f'{net_file}.rou.xml')
        self._routes = routes

    def generate_routefile(self, seed):
        np.random.seed(seed)  # make tests reproducible

        # the generation of cars is distributed according to a weibull distribution
        timings = np.random.weibull(2, self._n_cars)
        timings = np.sort(timings)

        # reshape the distribution to fit the interval 0:max_steps
        car_gen_steps = []
        min_old = math.floor(timings[1])
        max_old = math.ceil(timings[-1])
        min_new = 0
        max_new = self._max_steps
        for value in timings:
            car_gen_steps = np.append(car_gen_steps, ((max_new - min_new) / (max_old - min_old)) * (value - max_old) + max_new)

        car_gen_steps = np.rint(car_gen_steps)  # round every value to int -> effective steps when a car will be generated

        vehicle_type = "standard_car"
        # produce the file for cars generation, one car per line
        with open(self._route_file, "w") as file:
            print("""<routes>
            <vType accel="1.0" decel="4.5" id="standard_car" length="5.0" minGap="2.5" maxSpeed="25" sigma="0.5" />

            <route id="E_to_W" edges="right_in left_out"/>
            <route id="W_to_E" edges="left_in right_out"/>""", file=file)

            e_counter = 0
            w_counter = 0
            half = self._n_cars / 2
            for car_counter, step in enumerate(car_gen_steps):
                if np.random.randint(0,2) == 0:
                    if e_counter < half:
                        print(f'    <vehicle id="E_to_W_{car_counter}" type="{vehicle_type}" route="E_to_W" depart="{step}" departLane="random" />', file=file)
                        e_counter += 1
                    else:
                        print(f'    <vehicle id="W_to_E_{car_counter}" type="{vehicle_type}" route="W_to_E" depart="{step}" departLane="random" />', file=file)
                        w_counter += 1
                else:
                    if w_counter < half:
                        print(f'    <vehicle id="W_to_E_{car_counter}" type="{vehicle_type}" route="W_to_E" depart="{step}" departLane="random" />', file=file)
                        w_counter += 1
                    else:
                        print(f'    <vehicle id="W_to_E_{car_counter}" type="{vehicle_type}" route="W_to_E" depart="{step}" departLane="random" />', file=file)
                        w_counter += 1
            getLogger().info(f'Cars East: {e_counter} West: {w_counter}')
            print("</routes>", file=file)

test = Routing(1000, 3600, '1TL/1TL', [None])
test.generate_routefile(0)