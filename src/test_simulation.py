import traci
import timeit
import numpy as np

from config import set_sumo
from logger import getLogger

class TestSimulation():
    def __init__(self, AGENT, gui, max_step, green_duration, yellow_duration, input_dim, config_file):
        self._AGENT = AGENT
        self._sumo_cmd = set_sumo(gui, config_file)
        self._input_dim = input_dim
        self._num_actions = 4
        self._num_lanes = 16
        self._step = 0
        self._max_steps = max_step
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration

        #stats
        self._reward_store = []
        self._wait_store = {}
        self._distance_store = {}
        self._queue_length = []
    
    def run(self):
        start_time = timeit.default_timer()

        traci.start(self._sumo_cmd)
        getLogger().info('Simulating...')

        #init
        self._step = 0
        self._waiting_times = {}
        trafficlight_list = traci.trafficlight.getIDList()
        trafficlight_count = len(trafficlight_list)
        old_total_wait = np.zeros(trafficlight_count)
        action = np.zeros(trafficlight_count)
        old_action = np.zeros(trafficlight_count)
        reward = np.zeros(trafficlight_count)

        # for tl in trafficlight_list:
        #     getLogger().info(f'TrafficLightID: {tl} -> Controlled lanes: {self._get_controlled_lanes(tl)}')

        while self._step < self._max_steps:
            for index, trafficlight_id in enumerate(trafficlight_list):
                if traci.trafficlight.getNextSwitch(trafficlight_id) - traci.simulation.getTime()  <= 0:
                    
                    if self.isGreen(traci.trafficlight.getPhase(trafficlight_id)): #GREEN PHASE
                        current_state = self._get_state(int(action[index]), trafficlight_id)
                        action[index] = self._choose_action(current_state)
                        # getLogger().info(f'Step: {self._step} TraffigcLightID: {trafficlight_id} New Action: {action[index]} Old Action: {old_action[index]} Current Phase:{traci.trafficlight.getPhase(trafficlight_id)/2}')
                        current_total_wait = self._get_waiting_time(trafficlight_id)
                        reward[index] = old_total_wait[index] - current_total_wait

                        #different phase
                        if self._step != 0 and old_action[index] != action[index]:
                            self._set_yellow_phase(old_action[index] , trafficlight_id)
                        else:
                            self._set_green_phase(action[index] , trafficlight_id)
                        
                        old_action[index]  = action[index] 
                        old_total_wait[index] = current_total_wait

                        self._reward_store.append(reward[index])
                        queue_length = self._get_queue_length(trafficlight_id)
                        self._queue_length.append(queue_length)

                    else: #YELLOW PHASE
                        self._set_green_phase(action[index] , trafficlight_id)
            
            self._save_stats()
            traci.simulationStep()
            self._step += 1
                
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time
    
    def _get_state(self, action, trafficlight_id): #GET STATE FROM SUMO
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
            getLogger.debug(f'There are no action: {action}')

        lanes = self._get_controlled_lanes(trafficlight_id)
        # getLogger().info(f'TrafficLightID: {trafficlight_id} Lanes: {lanes}')

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

        # getLogger().info(f'pos: {position_matrix} vel: {velocity_matrix}, phase: {phase_matrix}')
        return [position_matrix, velocity_matrix, phase_matrix]
    
    def _choose_action(self, state): #CHOOSE ACTION
        action = np.argmax(self._AGENT.predict_one(state))
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
    
    def _get_waiting_time(self, trafficlight_id): #GET ALL WAITING TIME FOR ALL INCOMING LANES
        car_list = traci.vehicle.getIDList()

        lanes = self._get_controlled_lanes(trafficlight_id)
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
    
    def _get_queue_length(self, trafficlight_id): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        queue_length = 0

        lanes = self._get_controlled_lanes(trafficlight_id)
        for l in lanes:
            queue_length = queue_length + traci.lane.getLastStepHaltingNumber(l)

        return queue_length
    
    def _save_stats(self):
        car_list = traci.vehicle.getIDList()

        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            distance = traci.vehicle.getDistance(car_id)

            self._wait_store[car_id] = round(wait_time, 2)
            self._distance_store[car_id] = round(distance, 2)
    
    def get_stats(self):
        wait_list = list(self._wait_store.values())
        distance_list = list(self._distance_store.values())

        return np.array(wait_list), np.array(distance_list)

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
    
    def isGreen(self, index): #IF PHASE IS GREEN
        if (index % 2) == 0:
            return True
        else:
            return False
    
    def average_queue_length(self):
        return round(sum(self._queue_length)/len(self._queue_length), 2)
    
    def average_waiting_time(self):
        return round(sum(self._wait_store)/len(self._wait_store), 2), self._min_wait_time, self._max_wait_time

    @property
    def reward_store(self):
        return self._reward_store
