import sys
import traci
import timeit
import random
import numpy as np

from agent import Agent
from config import set_sumo
from logger import getLogger
from routing import Routing
from interface.trafficlight import TrafficLight

class TrainSimulation:
    def __init__(self, gui, epochs, gamma, max_step, green_duration, yellow_duration, input_dim, num_cars, config_file, config_input):
        self._sumo_cmd = set_sumo(gui, config_file)
        self._sumo_intersection = Routing(num_cars, max_step)
        self._input_dim = input_dim
        self._max_steps = max_step
        self._epochs = epochs
        self._gamma = gamma
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
        self._config_file = config_file
        self._config_input = config_input

        self._trafficlight_list = []
        self._num_actions = 0
        self._num_lanes = 0
        self._step = 0

        #stats
        self._reward_store = []
        self._cumulative_wait_store = []
        self._avg_queue_length_store = []
    
    '''
    AGENT MODEL
    '''
    def configure_model(self, input_dim, num_layers, batch_size, learning_rate, size_min, size_max):

        traffic_lights = traci.trafficlight.getIDList()
        getLogger().info(f'Number of traffic lights detected: {len(traffic_lights)} ID: {traffic_lights}')

        for tl in traffic_lights:
            lanes = self._get_controlled_lanes(tl)
            self._num_lanes = len(lanes)
            phases = traci.trafficlight.getAllProgramLogics(tl)
            self._num_actions = int(len(phases[0].getPhases()) / 2)

            agent = Agent(input_dim, self._num_actions, num_layers, batch_size, learning_rate, self._num_lanes, size_min, size_max)
            self._trafficlight_list.append(TrafficLight(tl, lanes, agent))

    '''
    SUMO INTERACTIONS
    '''
    def run(self, episode, epsilon): #START SIMULATION
        traci.start(self._sumo_cmd)

        if not self._trafficlight_list:
            self.configure_model(
                self._config_input['input_dim'],
                self._config_input['num_layers'],
                self._config_input['batch_size'],
                self._config_input['learning_rate'],
                self._config_input['size_min'],
                self._config_input['size_max']
            )

        start_time = timeit.default_timer()
        self._sumo_intersection.generate_routefile(episode)
        getLogger().info('Simulating...')

        #init
        self._step = 0
        self._waiting_times = {}
        self._sum_reward = 0
        self._sum_queue_length = 0
        self._sum_waiting_time = 0

        for tl in self._trafficlight_list:
            tl.reset_data()

        while self._step < self._max_steps:
            for tl in self._trafficlight_list:
                current_state = self._get_state(tl.action, tl.lanes)
                current_total_wait = self._get_waiting_time(tl.lanes)
                tl.reward = tl.old_total_wait - current_total_wait

                #save data to memory
                if self._step != 0:
                    tl.agent.add_sample((tl.old_state, tl.old_action, tl.reward, current_state))
            
                #traffic light phase
                tl.action = self._choose_action(current_state, epsilon, tl.agent)

                #different phase
                if self._step != 0 and tl.old_action != tl.action:
                    self._set_yellow_phase(tl.old_action, tl.id)
                    self._simulate(self._yellow_duration)
                
                self._set_green_phase(tl.action, tl.id)
                self._simulate(self._green_duration)

                tl.old_state = current_state
                tl.old_action = tl.action
                tl.old_total_wait = current_total_wait

                if tl.reward < 0:
                    self._sum_reward += tl.reward
            
        self._save_stats() #Save
        getLogger().info(f'Total reward: {self._sum_reward} - Epsilon: {round(epsilon, 2)}')
        getLogger().info(f'Queue Length: {self._sum_queue_length / self._max_steps} - Sum Waiting Time: {self._sum_waiting_time}')

        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)
        training_time = 0

        for tl in self._trafficlight_list:
            self.tl.agent.reset_data() #Clear loss and accuracy data from agent
            start_time = timeit.default_timer()

            for _ in range(self._epochs):
                self._replay(tl.agent)
            training_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time, training_time
    
    def _get_state(self, action, lanes): #GET STATE FROM SUMO
        #init
        position_matrix = np.zeros((self._num_lanes, self._input_dim))
        velocity_matrix = np.zeros((self._num_lanes, self._input_dim))
        phase_matrix = np.zeros(4)
        cell_length = 7
        offset = 1

        #phase matrix based on current active traffic light phase
        if action < 4:
            phase_matrix[action] = 1
        else:
            getLogger().debug(f'Incorrect Green phase action: {action} from getState()')

        for index, l in enumerate(lanes):
            lane_length = traci.lane.getLength(l)
            vehicles = traci.lane.getLastStepVehicleIDs(l)

            for v in vehicles:
                lane_pos = traci.vehicle.getLanePosition(v)
                target_pos = lane_length - (self._input_dim * cell_length)

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
    
    def _replay(self, agent): #STORE TO AGENT MEMORY
        batch = agent.get_samples(agent._batch_size)

        if len(batch) > 0:  # if memory is full
            states = ([val[0] for val in batch])
            next_states = ([val[3] for val in batch])

            # prediction
            q = agent.predict_batch(states)
            q_next = agent.predict_batch(next_states) 

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

            agent.train_batch(x, y)  # train the NN
    
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
        
    
    def _choose_action(self, state, epsilon, agent): #CHOOSE ACTION
        action = 0

        if random.random() < epsilon:
            action = random.randint(0, self._num_actions - 1) #explore
        else:
            action = np.argmax(agent.predict_one(state)) #exploit
        
        # getLogger().info(f'Action: {action}')
        return action

    '''
    UTILS
    '''  
    def _set_yellow_phase(self, action, trafficlight_id): #CHANGE PHASE TO YELLOW
        phase_code = action * 2 + 1
        traci.trafficlight.setPhase(trafficlight_id, phase_code)
    
    def _set_green_phase(self, action, trafficlight_id): #CHANGE PHASE TO GREEN
        if action == 0:
            traci.trafficlight.setPhase(trafficlight_id, action * 2)
        elif action == 1:
            traci.trafficlight.setPhase(trafficlight_id, action * 2)
        elif action == 2:
            traci.trafficlight.setPhase(trafficlight_id, action * 2)
        elif action == 3:
            traci.trafficlight.setPhase(trafficlight_id, action * 2)
        else:
            getLogger().debug(f'Incorrect Green phase action: {action}')
    
    def _get_waiting_time(self, lanes): #GET ALL WAITING TIME FOR ALL INCOMING LANES
        car_list = traci.vehicle.getIDList()

        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getLaneID(car_id)        
            if road_id in lanes:
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times: #if car has left the intersection
                    del self._waiting_times[car_id]

        total_waiting_time = sum(self._waiting_times.values())
        
        return total_waiting_time
    
    def _get_queue_length(self): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        queue_length = 0

        lanes = self._get_controlled_lanes("TL")
        for l in lanes:
            queue_length = queue_length + traci.lane.getLastStepHaltingNumber(l)
        
        return queue_length
    
    def _save_stats(self):
        self._reward_store.append(self._sum_reward)
        self._cumulative_wait_store.append(self._sum_waiting_time)  # total number of seconds waited by cars in this episode
        self._avg_queue_length_store.append(self._sum_queue_length / self._max_steps) 

    def _get_controlled_lanes(self, traffic_light_id): #GET ALL CONTROLLED LANES OF THE TRAFFIC LIGHT
        lanes = traci.trafficlight.getControlledLanes(traffic_light_id)
        temp_list = []
        for i in lanes: #remove duplicate
            if i not in temp_list:
                temp_list.append(i)
        lanes = temp_list
        return lanes

    def _get_lane_id(self, lane_id): #GET LAST CHARRACTER OF A STRING
        return int(lane_id[len(lane_id)-1])

    @property
    def reward_store(self):
        return self._reward_store
    
    @property
    def cumulative_wait_store(self):
        return self._cumulative_wait_store

    @property
    def avg_queue_length_store(self):
        return self._avg_queue_length_store