import numpy as np

class Routing:
    def __init__(self, n_cars, max_step):
        self._n_cars = n_cars #number of cars per episode
        self._max_steps = max_step
    
    def generate_routefile(self, seed):
        '''
        Generate car routes
        '''
        np.random.seed(seed)

        with open("../sumo_files/routes.rou.xml", "w") as routes:
            print('''<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/netconvertConfiguration.xsd">
            <vType accel="1.0" decel="4.5" id="standard_car" length="5.0" minGap="2.5" maxSpeed="25" sigma="0.5" />

            <route id="East_to_North" edges="right_in top_out/>
            <route id="East_to_West" edges="right_in left_out/>
            <route id="East_to_South" edges="right_in bottom_out/>
            <route id="West_to_North" edges="left_in top_out/>
            <route id="West_to_East" edges="left_in right_out/>
            <route id="West_to_South" edges="left_in bottom_out/>
            <route id="North_to_East" edges="top_in right_out/>
            <route id="North_to_South" edges="top_in bottom_out/>
            <route id="North_to_West" edges="top_in left_out/>
            <route id="South_to_East" edges="bottom_in right_out/>
            <route id="South_to_North" edges="bottom_in top_out/>
            <route id="South_to_West" edges="bottom_in left_out/>

            ''', file=routes)

