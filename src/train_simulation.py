import os
import sys
import traci
import timeit
import random
import numpy as np

from agent import Agent
from routing import Routing
from logger import getLogger
from tools import get_trafficlightID, set_sumo, create_routes, get_num_lanes
from interface.trafficlight import TrafficLight

class TrainSimulation:
    def __init__(self, config):
        self._config = config
        self._sumo_file = config['sumo_file']
        self._sumo_cmd = set_sumo(config['sumo_gui'], self._sumo_file)
        self._green_duration = config['green_duration']
        self._yellow_duration = config['yellow_duration']
        self._input_dim = config['input_dim']
        self._max_steps = config['max_step']
        self._epochs = config['epochs']
        self._gamma = config['gamma']
        self._configure_settings(config)
        self._trafficlight_list = []
        
    '''
    AGENT MODEL AND ROUTING
    '''
    def _configure_settings(self, config):
        net_path = config['sumo_file']
        net_path = os.path.join('sumo_files', f'{net_path}.net.xml')
        trafficlights =  get_trafficlightID(net_path)
        self._sumo_intersection = Routing(config['num_cars'], config['max_step'], config['sumo_file'], create_routes(trafficlights[0]))
    
    def _configure_model(self, net_path):
        net_path = os.path.join('sumo_files', f'{net_path}.net.xml')
        trafficlights =  get_trafficlightID(net_path)
        for tl in trafficlights:
            num_lanes = get_num_lanes(tl)
            logic = traci.trafficlight.getAllProgramLogics(tl.getID())
            tls_program = logic[0].getPhases()
            output_dim = int(len(tls_program) / 2)
            agent = Agent(self._config, output_dim, num_lanes)
            lanes = self._get_controlled_lanes(tl.getID())
            phases = []
            for i in range(0, len(tls_program), 2):
                phases.append(tls_program[i].state)
            self._trafficlight_list.append(TrafficLight(tl.getID(), agent, lanes, phases, output_dim))
        
    '''
    SUMO INTERACTIONS
    '''
    def run(self, episode, epsilon): #START SIMULATION
        self._sumo_intersection.generate_routefile(episode)
        traci.start(self._sumo_cmd)

        start_time = timeit.default_timer()
        getLogger().info('Simulating...')

        #init
        self._step = 0
        self._waiting_times = {}   

        if not self._trafficlight_list:
            self._configure_model(self._sumo_file)

        while self._step < self._max_steps:
            for tl in self._trafficlight_list:
                if traci.trafficlight.getNextSwitch(tl.id) - traci.simulation.getTime()  <= 0: # If trafficlight duration reaches zero
                    if self.isGreen(traci.trafficlight.getRedYellowGreenState(tl.id)): #GREEN PHASE   
                        current_state = self._get_state(tl)
                        current_total_wait = self._get_waiting_time(tl.lanes)

                        '''
                        #calculate reward
                        cars_passed = self._get_car_passtrough(tl.car_present, self._get_cars_in_lane(tl.lanes))
                        tl.car_present = self._get_cars_in_lane(tl.lanes)
                        queue_length = self._get_queue_length(tl.lanes)
                        if queue_length != 0:
                            plus_reward = cars_passed / queue_length
                        else:
                            plus_reward = cars_passed
                        tl.reward = tl.old_total_wait - current_total_wait + (plus_reward * (self._green_duration + self._yellow_duration))
                        '''
                        
                        tl.reward = tl.old_total_wait - current_total_wait

                        #save data to memory
                        if self._step != 0:
                            tl.agent.add_sample((tl.old_state, tl.old_action, tl.reward, current_state))
                
                        #traffic light phase
                        tl.action = self._choose_action(current_state, epsilon, tl)

                        #different phase
                        if self._step != 0 and tl.old_action != tl.action:
                            self._set_yellow_phase(tl)
                        else:
                            self._set_green_phase(tl)

                        tl.old_state = current_state
                        tl.old_action = tl.action
                        tl.old_total_wait = current_total_wait

                        if tl.reward < 0:
                            tl.sum_reward += tl.reward
                    else: #YELLOW PHASE
                        self._set_green_phase(tl)
                elif self._step == 0:
                    tl.old_state =  self._get_state(tl)
                    
                queue_length = self._get_queue_length(tl.lanes)
                tl.sum_queue_length += queue_length
                tl.sum_waiting_time += queue_length

            traci.simulationStep()
            self._step += 1     

        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)
        training_time = 0
        getLogger().info(f'Epsilon: {round(epsilon, 2)}')

        for tl in self._trafficlight_list:
            #Save episode stats
            tl.save_stats(self._max_steps)
            getLogger().info(f'Queue Length: {round(tl.sum_queue_length / self._max_steps, 2)} Sum Waiting Time: {tl.sum_waiting_time}  Total nagative reward: {tl.sum_reward}')
            tl.reset_data()

            start_time = timeit.default_timer()
            for _ in range(self._epochs):
                self._replay(tl)
            training_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time, training_time
    
    def _get_state(self, tl): #GET STATE FROM SUMO
        #init
        position_matrix = np.zeros((tl.agent.num_lanes, self._input_dim))
        velocity_matrix = np.zeros((tl.agent.num_lanes, self._input_dim))
        phase_matrix = np.zeros(tl.action_dim)
        cell_length = 7

        #phase matrix based on current active traffic light phase
        if tl.action < tl.action_dim:
            phase_matrix[tl.action] = 1
        else:
            getLogger().debug(f'Incorrect Green phase action: {tl.action} from getState()')

        for index, l in enumerate(tl.lanes):
            lane_length = traci.lane.getLength(l)
            vehicles = traci.lane.getLastStepVehicleIDs(l)

            for v in vehicles:
                lane_pos = traci.vehicle.getLanePosition(v)
                target_pos = lane_length - (self._input_dim * cell_length)

                if lane_pos > target_pos: #if vehicle is close to the traffic light
                    speed = round(traci.vehicle.getSpeed(v) / traci.lane.getMaxSpeed(l), 2)

                    #([lane][position])
                    index_1 = int((lane_length - lane_pos) / cell_length)
                    position_matrix[index][index_1] = 1
                    velocity_matrix[index][index_1] = speed

        # getLogger().info(f'Pos: {position_matrix} \n Vel: {velocity_matrix} \n Phase: {phase_matrix}')
        return [position_matrix, velocity_matrix, phase_matrix]
    
    def _replay(self, tl): #STORE TO AGENT MEMORY
        batch = tl.agent.get_samples(tl.agent._batch_size)

        if len(batch) > 0:  # if memory is full
            states = ([val[0] for val in batch])
            next_states = ([val[3] for val in batch])

            # prediction
            q = tl.agent.predict_batch(states)
            q_next = tl.agent.predict_batch(next_states) 

            # setup training arrays
            x = []
            y = np.zeros((len(batch), tl.action_dim))

            for i, b in enumerate(batch):
                state, action, reward, _ = b[0], b[1], b[2], b[3]
                current_q = q[i] 
                current_q[action] = reward + self._gamma * np.amax(q_next[i])  # update Q(state, action)

                x.append(state)
                y[i] = current_q  # Q(state)

            tl.agent.train_batch(x, y)  # train the NN            
    
    def _choose_action(self, state, epsilon, tl): #CHOOSE ACTION
        action = 0
        if random.random() < epsilon:
            action = random.randint(0, tl.action_dim - 1) #explore
        else:
            action = np.argmax(tl.agent.predict_one(state)) #exploit
        return action
        
    '''
    UTILS
    '''  
    def _set_yellow_phase(self, tl): #CHANGE PHASE TO YELLOW
        current_phase = traci.trafficlight.getRedYellowGreenState(tl.id)
        result_phase = tl.phases[tl.action]
        next_phase = []
        for x, y in zip(current_phase, result_phase):
            if x == 'G' and y =='r':
                next_phase.append('y')
            else:
                next_phase.append(x)
        next_phase = "".join(next_phase)
        traci.trafficlight.setRedYellowGreenState(tl.id, next_phase)
        traci.trafficlight.setPhaseDuration(tl.id, self._yellow_duration)
    
    def _set_green_phase(self, tl): #CHANGE PHASE TO GREEN
        if tl.action < len(tl.lanes):
            traci.trafficlight.setRedYellowGreenState(tl.id, tl.phases[tl.action])
        else:
            msg = f'Incorrect trafficlight action: {tl.action} of {len(tl.phases)}'
            getLogger().error(msg)
            sys.error(msg)
        traci.trafficlight.setPhaseDuration(tl.id, self._green_duration)
    
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
    
    def _get_queue_length(self, lanes): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        queue_length = 0
        for l in lanes:
            queue_length = queue_length + traci.lane.getLastStepHaltingNumber(l)
        return queue_length
    
    def _get_cars_in_lane(self, lanes):
        cars = []
        for l in lanes:
            cars.append(traci.lane.getLastStepVehicleIDs(l))
        return cars
    
    def _get_car_passtrough(self, old, current):
        count = 0
        for o in old:
            if o in current:
                continue
            else:
                count += 1
        return count
    
    def isGreen(self, phase): #IF PHASE IS GREEN
        if 'y' in phase:
            return False
        else:
            return True
        
    def _get_controlled_lanes(self, traffic_light_id): #GET ALL CONTROLLED LANES OF THE TRAFFIC LIGHT
        lanes = traci.trafficlight.getControlledLanes(traffic_light_id)
        temp_list = []
        for i in lanes: #remove duplicate
            if i not in temp_list:
                temp_list.append(i)
        lanes = temp_list
        return lanes

    @property
    def traffic_light_list(self):
        return self._trafficlight_list
