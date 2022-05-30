import traci
import sumolib
import timeit
import random
import numpy as np

from agent import Agent
from tools import set_sumo
from logger import getLogger
from routing import Routing
from interface.trafficlight import TrafficLight

class TrainSimulation:
    def __init__(self, agent, config):
        self._agent = agent
        self._config_file = config['sumocfg_file']
        self._sumo_cmd = set_sumo(config['sumo_gui'], self._config_file)
        self._sumo_intersection = Routing(config['num_cars'], config['max_step'])
        self._green_duration = config['green_duration']
        self._yellow_duration = config['yellow_duration']
        self._input_dim = config['input_dim']
        self._output_dim = config['output_dim']
        self._max_steps = config['max_step']
        self._epochs = config['epochs']
        self._gamma = config['gamma']
        
        self.configure_model(config['num_lanes'])
    
    '''
    AGENT MODEL
    '''
    def configure_model(self, num_lanes):
        self._trafficlight_list = []
        path = 'sumo_files/Train_env/environment.net.xml'
        net = sumolib.net.readNet(path)
        traffic_lights = net.getTrafficLights()
        for tl in traffic_lights:
            self._trafficlight_list.append(TrafficLight(tl.getID(),num_lanes,self._agent))

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
        self._sum_reward = 0
        self._sum_queue_length = 0
        self._sum_waiting_time = 0

        if self._step == 0:
            self._trafficlight_list[0].lanes = self._get_controlled_lanes(self._trafficlight_list[0].id)         

        while self._step < self._max_steps:
            for tl in self._trafficlight_list:
                if traci.trafficlight.getNextSwitch(tl.id) - traci.simulation.getTime()  <= 0:
                    if self.isGreen(traci.trafficlight.getPhase(tl.id)):
                        current_state = self._get_state(tl)
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
                        else:
                            self._set_green_phase(tl.action, tl.id)

                        tl.old_state = current_state
                        tl.old_action = tl.action
                        tl.old_total_wait = current_total_wait

                        if tl.reward < 0:
                            tl.sum_reward += tl.reward
                    else: #YELLOW PHASE
                        self._set_green_phase(tl.action, tl.id)
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
                self._replay(tl.agent)
            training_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time, training_time
    
    def _get_state(self, tl): #GET STATE FROM SUMO
        #init
        position_matrix = np.zeros((tl.agent.num_lanes, self._input_dim))
        velocity_matrix = np.zeros((tl.agent.num_lanes, self._input_dim))
        phase_matrix = np.zeros(4)
        cell_length = 7

        #phase matrix based on current active traffic light phase
        if tl.action < 4:
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

                    #([lane_id][position])
                    index_1 = index
                    index_2 = int((lane_length - lane_pos) / cell_length)

                    position_matrix[index_1][index_2] = 1
                    velocity_matrix[index_1][index_2] = speed

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
            y = np.zeros((len(batch), self._output_dim))

            for i, b in enumerate(batch):
                state, action, reward, _ = b[0], b[1], b[2], b[3]
                current_q = q[i] 
                current_q[action] = reward + self._gamma * np.amax(q_next[i])  # update Q(state, action)

                x.append(state)
                y[i] = current_q  # Q(state)

            agent.train_batch(x, y)  # train the NN            
    
    def _choose_action(self, state, epsilon, agent): #CHOOSE ACTION
        action = 0
        if random.random() < epsilon:
            action = random.randint(0, self._output_dim - 1) #explore
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
    
    def _get_queue_length(self, lanes): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        queue_length = 0
        for l in lanes:
            queue_length = queue_length + traci.lane.getLastStepHaltingNumber(l)
        return queue_length
    
    def isGreen(self, index): #IF PHASE IS GREEN
        if (index % 2) == 0:
            return True
        else:
            return False
        
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
