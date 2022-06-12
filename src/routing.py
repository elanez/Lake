import os
import sys
import numpy as np
import math

from logger import getLogger

class Routing:
    def __init__(self, n_cars, max_steps, net_file, routes):
        self._n_cars = n_cars #number of cars per episode
        self._max_steps = max_steps
        self._route_file = os.path.join('sumo_files', f'{net_file}.rou.xml')
        self._routes = routes
    
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

        route_straight = []
        route_turn = []
        vehicle_type = "standard_car"

        with open(self._route_file, "w") as file:
            print('''<routes>
    <vType accel="0.8" id="standard_car" decel="4.5" length="5.0" minGap="2.5" maxSpeed="16.67" sigma="0.5" />
    ''', file=file)

            '''
            ROUTE CREATION
            <route id="{edge_incoming}_to_{edge_outgoing}" edges="{edge_incoming} {edge_outgoing}"/>
            bottom left top right
            '''
            for routes in self._routes:
                print(f'    <route id="{routes.id}" edges="{routes.edge_in.getID()} {routes.edge_out.getID()}" />', file=file)
            
            '''
            VEHICLE CREATION
            <vehicles id="{route_id}_{car_counter}" type="{vehicle_type}" route="{route_id}" depart="{step}" departLane="random" />
            '''
            #Split routes into straight and turn
            for route in self._routes:
                if route.type == 'straight':
                    route_straight.append(route.id)
                elif route.type == 'turn':
                    route_turn.append(route.id)
                else:
                    msg = f'Route type error: {route.type}'
                    getLogger().error(msg)
                    sys.error(msg)
            for car_counter, step in enumerate(car_gen_steps):
                if np.random.uniform() < 0.75: #car goes straight -> 75%
                    i = np.random.randint(0, len(route_straight)) # random source and destination
                    print(f'    <vehicle id="{route_straight[i]}_{car_counter}" type="{vehicle_type}" route="{route_straight[i]}" depart="{step}" departLane="random" />', file=file)
                else: #car turns
                    i = np.random.randint(0, len(route_turn)) # random source and destination
                    print(f'    <vehicle id="{route_turn[i]}_{car_counter}" type="{vehicle_type}" route="{route_turn[i]}" depart="{step}" departLane="random" />', file=file)
            print('</routes>', file=file)
