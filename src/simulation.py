import os
import sys
import numpy as np
import random
import timeit
import traci

from logger import getLogger
from routing import Routing
from sumolib import checkBinary

#PHASE CODE from SUMO
PHASE_EW_GREEN = 0
PHASE_EW_YELLOW = 1
PHASE_EWS_GREEN = 2
PHASE_EWS_YELLOW = 3
PHASE_NS_GREEN = 4
PHASE_NS_YELLOW = 5
PHASE_NSS_GREEN = 6
PHASE_NSS_YELLOW = 7

class Simulation:
    def __init__(self, AGENT):
        self._AGENT = AGENT
        self._sumo_cmd = self._set_sumo(False, 'sumo_config.sumocfg') #(gui, filename)
        self._sumo_intersection = Routing(1000, 3600) #(number of cars, max steps)
        self._num_states = 16
        self._num_actions = 4
        self._step = 0
        self._max_steps = 3600
        self._epochs = 10
        self._gamma = 0.75 #discount rate

    '''
    SUMO INTERACTIONS
    '''
    def run(self, episode, epsilon): #START SIMULATION
        start_time = timeit.default_timer()

        self._sumo_intersection.generate_routefile(episode)
        traci.start(self._sumo_cmd)
        getLogger().info('Simulating...')

        #init
        self._step = 0
        self._waiting_times = {}
        self._sum_reward = 0
        self._sum_queue_length = 0
        self._sum_waiting_time = 0
        action = 0
        old_total_wait = 0
        old_state = -1
        old_action = -1

        while self._step < self._max_steps:
            current_state = self._get_state(action)
            # getLogger().info(f'Current State: {current_state}')

            current_total_wait = self._get_waiting_time()
            reward = old_total_wait - current_total_wait

            #save data to memory
            if self._step != 0:
                self._AGENT.add_sample((old_state, old_action, reward, current_state))
            
            #traffic light phase
            action = self._choose_action(current_state, epsilon)

            #different phase
            if self._step != 0 and old_action != action:
                self._set_yellow_phase(old_action)
                self._simulate(3)
            
            self._set_green_phase(action)
            self._simulate(30)

            old_state = current_state
            old_action = action
            old_total_wait = current_total_wait

            if reward < 0:
                self._sum_reward += reward

        getLogger().info(f'Total reward: {self._sum_reward} - Epsilon: {round(epsilon, 2)}')
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        # getLogger().info('Training ...')
        start_time = timeit.default_timer()
        for _ in range(self._epochs):
            self._replay()
        training_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time, training_time
    
    def _get_state(self, action): #GET STATE FROM SUMO
        #init
        position_matrix = np.zeros((self._num_states, 16))
        velocity_matrix = np.zeros((self._num_states, 16))
        phase_matrix = np.zeros(4)
        cell_length = 7
        offset = 1

        #current active traffic light phase
        if action < 4:
            phase_matrix[action] = 1
        else:
            getLogger().debug(f'Incorrect Green phase action: {action} from getState()')

        traffic_light = traci.trafficlight.getIDList()

        for tl in traffic_light:
            lanes = self._get_controlled_lanes(tl)

            for index, l in enumerate(lanes):
                lane_length = traci.lane.getLength(l)
                vehicles = traci.lane.getLastStepVehicleIDs(l)

                for v in vehicles:
                    lane_pos = traci.vehicle.getLanePosition(v)
                    target_pos = lane_length - (self._num_states * cell_length)

                    if lane_pos > target_pos: #if vehicle is close to the traffic light
                        speed = round(traci.vehicle.getSpeed(v) / traci.lane.getMaxSpeed(l), 2)

                        #([lane_id][position])
                        index_1 = self._get_lane_id(l) * offset
                        index_2 = int((lane_length - lane_pos) / cell_length)

                        position_matrix[index_1][index_2] = 1
                        velocity_matrix[index_1][index_2] = speed
                
                if index == 3 + (4 * (offset - 1)):
                    offset += 1

        # getLogger().info(f'Pos: {position_matrix} \n Vel: {velocity_matrix} \n Phase: {phase_matrix}')

        return [position_matrix, velocity_matrix, phase_matrix]
    
    def _replay(self): #STORE TO AGENT MEMORY
        batch = self._AGENT.get_samples(self._AGENT._batch_size)

        if len(batch) > 0:  # if memory is full
            states = ([val[0] for val in batch])
            next_states = ([val[3] for val in batch])

            # prediction
            q = self._AGENT.predict_batch(states)
            q_next = self._AGENT.predict_batch(next_states) 

            # setup training arrays
            x = []
            y = np.zeros((len(batch), self._num_actions))
            # getLogger().info(f'x shape: {x.shape}, y shape: {y.shape}')

            for i, b in enumerate(batch):
                state, action, reward, _ = b[0], b[1], b[2], b[3]
                current_q = q[i] 
                current_q[action] = reward + self._gamma * np.amax(q_next[i])  # update Q(state, action)

                x.append(state)
                y[i] = current_q  # Q(state)

            self._AGENT.train_batch(x, y)  # train the NN
    
    def _simulate(self, steps_todo): #RUN SUMO SIMULATION
        if (self._step + steps_todo) >= self._max_steps: 
            steps_todo = self._max_steps - self._step
        
        while steps_todo > 0:
            traci.simulationStep()  # simulate 1 step in sumo
            self._step += 1
            steps_todo -= 1
            queue_length = self._get_queue_length()
            self._sum_queue_length += queue_length
            self._sum_waiting_time += queue_length 
        
    
    def _choose_action(self, state, epsilon): #CHOOSE ACTION
        action = 0
        if random.random() < epsilon:
            # getLogger().info('Agent chooses to explore')
            action = random.randint(0, self._num_actions - 1) #explore
        else:
            # getLogger().info('Agent chooses to exploit')
            action = np.argmax(self._AGENT.predict_one(state)) #exploit
        # getLogger().info(f'Action: {action}')
        return action

    '''
    UTILS
    '''
    def _set_sumo(self, gui, sumocfg_filename): #CONFIGURE SUMO
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            error_message = "please declare environment variable 'SUMO_HOME'"
            getLogger().critical(error_message)
            sys.exit(error_message)
        
        if gui == True:
            sumoBinary = checkBinary('sumo-gui')
        else:
            sumoBinary = checkBinary('sumo')

        return [sumoBinary, "-c", os.path.join('sumo_files', sumocfg_filename)]
    
    def _set_yellow_phase(self, action): #CHANGE PHASE TO YELLOW
        phase_code = action * 2 + 1
        traci.trafficlight.setPhase("TL", phase_code)
    
    def _set_green_phase(self, action): #CHANGE PHASE TO GREEN
        if action == 0:
            traci.trafficlight.setPhase("TL", PHASE_EW_GREEN)
        elif action == 1:
            traci.trafficlight.setPhase("TL", PHASE_EWS_GREEN)
        elif action == 2:
            traci.trafficlight.setPhase("TL", PHASE_NS_GREEN)
        elif action == 3:
            traci.trafficlight.setPhase("TL", PHASE_NSS_GREEN)
        else:
            getLogger().debug(f'Incorrect Green phase action: {action}')
    
    def _get_waiting_time(self): #GET ALL WAITING TIME FOR ALL INCOMING LANES
        incoming_roads = ["top_in", "right_in", "left_in", "bottom_in"]
        car_list = traci.vehicle.getIDList()

        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)
            if road_id in incoming_roads:
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times: #if car has left the intersection
                    del self._waiting_times[car_id]
        
        total_waiting_time = sum(self._waiting_times.values())
        # getLogger().info(f'Total Wait time: {total_waiting_time}')
        return total_waiting_time
    
    def _get_queue_length(self): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        road_N = traci.edge.getLastStepHaltingNumber("top_in")
        road_E = traci.edge.getLastStepHaltingNumber("right_in")
        road_S = traci.edge.getLastStepHaltingNumber("bottom_in")
        road_W = traci.edge.getLastStepHaltingNumber("left_in")
        
        queue_length = road_N + road_E + road_S + road_W
        return queue_length

    def _get_controlled_lanes(self, traffic_light_id): #GET ALL CONTROLLED LANES OF THE TRAFFIC LIGHT
        lanes = traci.trafficlight.getControlledLanes(traffic_light_id)
        
        #remove duplicate
        temp_list = []
        for i in lanes:
            if i not in temp_list:
                temp_list.append(i)
        lanes = temp_list
        return lanes

    def _get_lane_id(self, lane_id): #GET LAST CHARRACTER OF A STRING
        return int(lane_id[len(lane_id)-1])