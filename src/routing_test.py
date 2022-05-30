import numpy as np
import math

from logger import getLogger


class Routing:
    def __init__(self, n_cars, max_steps):
        self._n_cars = n_cars #number of cars per episode
        self._max_steps = max_steps
    
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

        #array of directions 
        direction = ["East", "North", "West", "South"]

        #arrow of edge directions
        edge_direction = ["right", "top", "left", "bottom"]

        #array for the vehicle id (depends if straight or turn)
        straight_vehicle_id = []
        turn_vehicle_id = []

        #array for the vehicle routes (depends if straight or turn)
        straight_routes = []
        turn_routes = []

        #array of conditions (depends if straight or turn) -- this is the if else condition
        straight_conditions = [0, 2, 1, 3,]
        turn_conditions = [0, 1, 4, 5, 2, 3, 6, 7]

        #array for route id and route edges
        route_id = []
        route_edges = []

        # saved the vehicle type and departLane to an array (if we need to add vehicles / depart lanes )
        vehicle_type = ["standard_car"]
        depart_lane = ["random"]

        #Route file location
        path = "sumo_files/Train_env/routes.rou.xml"

        # saving as routes_test.rou.xml 
        with open(path, "w") as routes:
                print('''<routes> 
       <Type accel="0.8" id="standard_car" decel="4.5" length="5.0" minGap="2.5" maxSpeed="16.6667" sigma="0.5" />
                ''', file=routes)
                i = 1
                current_index = 0
                route_index = 0
                while i <= len(direction):
                        for index in range(len(direction)):
                                new_index = index + 1
                                if(new_index == len(direction)):
                                        new_index = 0
                                        current_index += 1
                                if(current_index != new_index and current_index < len(direction)):
                                        route_index +=1
                                        route_id.append(f'{direction[current_index]}_to_{direction[new_index]}')
                                        route_edges.append(f'{edge_direction[current_index]}_in {edge_direction[new_index]}_out')
                                        if((current_index % 2 == 0 and new_index % 2 == 0) or (current_index % 2 != 0 and new_index % 2 != 0)): 
                                                straight_routes.append(f'{direction[current_index]}_to_{direction[new_index]}')
                                                straight_vehicle_id.append(f'{direction[current_index][0]}_{direction[new_index][0]}_')
                                        else:
                                                turn_routes.append(f'{direction[current_index]}_to_{direction[new_index]}')
                                                turn_vehicle_id.append(f'{direction[current_index][0]}_{direction[new_index][0]}_')
                                        print(f'''       <route id="{route_id[route_index-1]}" edges="{route_edges[route_index-1]}" />''', file=routes)
                        i += 1

                for car_counter, step in enumerate(car_gen_steps):
                        if np.random.uniform() < 0.60: #car goes straight -> 60%
                                straight = np.random.randint(0, 4) # random source and destination
                                for s in straight_conditions:
                                        if(s == straight):
                                        #        print(f'if straight == {s}', file=routes) ## JUST TO CHECK IF CONDITION IS RIGHT DELETE THIS IF CORRECT 
                                               print(f'    <vehicle id="{straight_vehicle_id[straight_conditions.index(s)]}{car_counter}" type="{vehicle_type[0]}" route="{straight_routes[straight_conditions.index(s)]}" depart="{step}" departLane="{depart_lane[0]}" />', file=routes)
                        else: #car turns
                                turn = np.random.randint(0, 8) # random source and destination
                                for t in turn_conditions:
                                        if(t == turn):
                                                # print(f'if turn == {t}', file=routes) ## JUST TO CHECK IF CONDITION IS RIGHT DELETE THIS IF CORRECT 
                                                print(f'    <vehicle id="{turn_vehicle_id[turn_conditions.index(t)]}{car_counter}" type="{vehicle_type[0]}" route="{turn_routes[turn_conditions.index(t)]}" depart="{step}" departLane="{depart_lane[0]}" />', file=routes)

                print('</routes>', file=routes)
