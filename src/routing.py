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

        # getLogger().info(f'Current directory: {os.getcwd()}')

        with open("sumo_files/routes.rou.xml", "w") as routes:
            print('''<routes>
    <vType accel="1.0" id="standard_car" length="5.0" minGap="2.5" maxSpeed="60" sigma="0.5" />

    <route id="East_to_North" edges="right_in top_out"/>
    <route id="East_to_West" edges="right_in left_out"/>
    <route id="East_to_South" edges="right_in bottom_out"/>
    <route id="West_to_North" edges="left_in top_out"/>
    <route id="West_to_East" edges="left_in right_out"/>
    <route id="West_to_South" edges="left_in bottom_out"/>
    <route id="North_to_East" edges="top_in right_out"/>
    <route id="North_to_South" edges="top_in bottom_out"/>
    <route id="North_to_West" edges="top_in left_out"/>
    <route id="South_to_East" edges="bottom_in right_out"/>
    <route id="South_to_North" edges="bottom_in top_out"/>
    <route id="South_to_West" edges="bottom_in left_out"/>
           ''', file=routes)

            depart_speed = 'max'
            
            for car_counter, step in enumerate(car_gen_steps):
                if np.random.uniform() < 0.60: #car goes straight
                    straight = np.random.randint(0, 4) # random source and destination
                    if straight == 0:
                        print(f'    <vehicle id="E_W_{car_counter}" type="standard_car" route="East_to_West" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif straight == 1:
                        print(f'    <vehicle id="W_E_{car_counter}" type="standard_car" route="West_to_East" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif straight == 2:
                        print(f'    <vehicle id="N_S_{car_counter}" type="standard_car" route="North_to_South" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    else:
                        print(f'    <vehicle id="S_N_{car_counter}" type="standard_car" route="South_to_North" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                else: #car turns
                    turn = np.random.randint(0, 8) # random source and destination
                    if turn == 0:
                        print(f'    <vehicle id="E_N_{car_counter}" type="standard_car" route="East_to_North" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif turn == 1:
                        print(f'    <vehicle id="E_W_{car_counter}" type="standard_car" route="East_to_South" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif turn == 2:
                        print(f'    <vehicle id="W_N_{car_counter}" type="standard_car" route="West_to_North" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif turn == 3:
                        print(f'    <vehicle id="W_S_{car_counter}" type="standard_car" route="West_to_South" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif turn == 4:
                        print(f'    <vehicle id="N_E_{car_counter}" type="standard_car" route="North_to_East" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif turn == 5:
                        print(f'    <vehicle id="N_W_{car_counter}" type="standard_car" route="North_to_West" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    elif turn == 6:
                        print(f'    <vehicle id="S_E_{car_counter}" type="standard_car" route="South_to_East" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)
                    else:
                        print(f'    <vehicle id="S_W_{car_counter}" type="standard_car" route="South_to_West" depart="{step}" departLane="random" departSpeed="{depart_speed}" />', file=routes)

            print('</routes>', file=routes)