import os
import numpy as np
import math

from logger import getLogger

class Routing:
    def __init__(self, n_cars, max_steps, net_file):
        self._n_cars = n_cars #number of cars per episode
        self._max_steps = max_steps
        self._route_file = os.path.join('sumo_files', f'{net_file}.rou.xml')
    
    def generate_routefile(self, seed):
        # getLogger().info('Generate route file...')

        np.random.seed(seed)  # make tests reproducible

        #weibull distribution
        timings = np.random.weibull(2, self._n_cars)
        timings = np.sort(timings)

        # reshape the distribution
        car_gen_steps = []
        min_old = math.floor(timings[1])
        max_old = math.ceil(timings[-1])
        min_new = 0
        max_new = self._max_steps
        for value in timings:
            car_gen_steps = np.append(car_gen_steps, ((max_new - min_new) / (max_old - min_old)) * (value - max_old) + max_new)

        # round every value to int
        car_gen_steps = np.rint(car_gen_steps)

        '''
        INSERT EDGES HERE
        Format:
            4 directions: [Noth, East, South, West]
            3 directions: [East, North/South, West] or [North, East/West, South]
        '''
        edge_in = ['top_in', 'right_in', 'bottom_in', 'left_in'] #incoming
        edge_out = ['top_out', 'right_out', 'bottom_out', 'left_out'] #outgoing
        routes = []
        route_straight = []
        route_turn = []
        vehicle_type = "standard_car"

        # getLogger().info(f'Current directory: {os.getcwd()}')
        with open(self._route_file, "w") as file:
            print('''<routes>
    <vType accel="0.8" id="standard_car" decel="4.5" length="5.0" minGap="2.5" maxSpeed="16.67" sigma="0.5" />
    ''', file=file)

            '''
            ROUTE CREATION
            <route id="{edge_incoming}_to_{edge_outgoing}" edges="{edge_incoming} {edge_outgoing}"/>
            '''
            for i, e_in in enumerate(edge_in):
               for j, e_out in enumerate(edge_out):
                    if i == j:
                       continue
                    else:
                        print(f'    <route id="{e_in}_to_{e_out}" edges="{e_in} {e_out}"/>', file=file)
                        routes.append(f'{e_in}_to_{e_out}')
            
            '''
            VEHICLE CREATION
            <vehicles id="{route_id}_{car_counter}" type="{vehicle_type}" route="{route_id}" depart="{step}" departLane="random" />
            '''
            #Split routes into straight and turn
            counter = 0
            for i, route in enumerate(routes):
                if i == 1 + (3 * counter):
                    route_straight.append(route)
                    counter += 1
                else:
                    route_turn.append(route)

            for car_counter, step in enumerate(car_gen_steps):
                if np.random.uniform() < 0.60: #car goes straight -> 60%
                    i = np.random.randint(0, len(route_straight)) # random source and destination
                    print(f'    <vehicles id="{route_straight[i]}_{car_counter}" type="{vehicle_type}" route="{route_straight[i]}" depart="{step}" departLane="random" />', file=file)
                else: #car turns
                    i = np.random.randint(0, len(route_turn)) # random source and destination
                    print(f'    <vehicle id="{route_turn[i]}_{car_counter}" type="{vehicle_type}" route="{route_turn[i]}" depart="{step}" departLane="random" />', file=file)
            print('</routes>', file=file)
