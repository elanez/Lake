import os
import sys
import traci
import timeit
import numpy as np

from agent import TestAgent
from logger import getLogger
from tools import get_trafficlightID, set_sumo, get_model_path, get_num_lanes
from interface.trafficlight import TrafficLight

class TestSimulation:
    def __init__(self, config):
        self._config = config
        self._sumo_file = config['sumo_file']
        self._sumo_cmd = set_sumo(config['sumo_gui'], self._sumo_file)
        self._green_duration = config['green_duration']
        self._yellow_duration = config['yellow_duration']
        self._input_dim = config['input_dim']
        self._max_steps = config['max_step']
        self._trafficlight_list = []
        
        #VEHICLE STATS
        self._distance = {}
        self._wait_time = {}
        
    '''
    AGENT MODEL
    '''
    def _configure_model(self, net_path):
        net_path = os.path.join('sumo_files', f'{net_path}.net.xml')
        trafficlights =  get_trafficlightID(net_path)
        for tl in trafficlights:
            num_lanes = get_num_lanes(tl)
            logic = traci.trafficlight.getAllProgramLogics(tl.getID())
            tls_program = logic[0].getPhases()

            input_dim = self._config['input_dim']
            output_dim = int(len(tls_program) / 2)
            model_id = f'model_{input_dim}.{num_lanes}.{output_dim}.h5'
            model_path = get_model_path(self._config['model_folder'])
            agent = TestAgent(model_id, input_dim, output_dim, num_lanes, os.path.join(model_path, tl.getID(), model_id))
            lanes = self._get_controlled_lanes(tl.getID())
            phases = []
            for i in range(0, len(tls_program), 2):
                phases.append(tls_program[i].state)
            self._trafficlight_list.append(TrafficLight(tl.getID(), agent, lanes, phases, output_dim))
        
    '''
    SUMO INTERACTIONS
    '''
    def run(self): #START SIMULATION
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
                if self._step == 0:
                    self._set_green_phase(tl)
                if traci.trafficlight.getNextSwitch(tl.id) - traci.simulation.getTime()  <= 0: # If trafficlight duration reaches zero
                    if self.isGreen(traci.trafficlight.getRedYellowGreenState(tl.id)): #GREEN PHASE   
                        current_state = self._get_state(tl)
                        # current_total_wait = self._get_waiting_time(tl.lanes)
                        
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
                
                        #traffic light phase
                        tl.action = self._choose_action(current_state, tl)
                        # tl.action_store.append(tl.action)

                        #different phase
                        if self._step != 0 and tl.old_action != tl.action:
                            self._set_yellow_phase(tl)
                        else:
                            self._set_green_phase(tl)

                        tl.old_state = current_state
                        tl.old_action = tl.action
                        # tl.old_total_wait = current_total_wait

                        # if tl.reward < 0:
                        #     tl.sum_reward += tl.reward
                    else: #YELLOW PHASE
                        self._set_green_phase(tl)
                elif self._step == 0:
                    tl.old_state =  self._get_state(tl)
                    
                # queue_length = self._get_queue_length(tl.lanes)
                # tl.sum_queue_length += queue_length
                # tl.sum_waiting_time += queue_length

            # self._save_vehicle_stats()
            traci.simulationStep()
            self._step += 1     

        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)
        '''
        for tl in self._trafficlight_list:
            #Save episode stats
            tl.save_stats(self._max_steps)
            getLogger().info(f'Queue Length: {round(tl.sum_queue_length / self._max_steps, 2)} Sum Waiting Time: {tl.sum_waiting_time}  Total nagative reward: {tl.sum_reward}')
            tl.reset_data()
        '''

        return simulation_time
    
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

                if lane_length - (self._input_dim * cell_length) < 0:
                    target_pos = lane_length
                else:
                    target_pos = lane_length - (self._input_dim * cell_length)

                if lane_pos > target_pos: #if vehicle is close to the traffic light
                    speed = round(traci.vehicle.getSpeed(v) / traci.lane.getMaxSpeed(l), 2)

                    #([lane][position])
                    index_1 = int((lane_length - lane_pos) / cell_length)
                    position_matrix[index][index_1] = 1
                    velocity_matrix[index][index_1] = speed

        # getLogger().info(f'Pos: {position_matrix} \n Vel: {velocity_matrix} \n Phase: {phase_matrix}')
        return [position_matrix, velocity_matrix, phase_matrix]     
    
    def _choose_action(self, state, tl):
        return np.argmax(tl.agent.predict_one(state))
        
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

    '''
    STATS
    '''
    def _save_vehicle_stats(self):
        car_list = traci.vehicle.getIDList()
        for car_id in car_list:
            distance = traci.vehicle.getDistance(car_id)
            if distance != 0:
                self._wait_time[car_id] = traci.vehicle.getAccumulatedWaitingTime(car_id)
                self._distance[car_id] = distance

    def get_vehicle_stats(self):
        return list(self._wait_time.values()), list(self._distance.values())

    @property
    def traffic_light_list(self):
        return self._trafficlight_list
