import os
import traci
import timeit
import random
import numpy as np

from tools import get_model_path
from agent import TestAgent
from tools import set_sumo
from logger import getLogger
from routing import Routing
from interface.trafficlight import TrafficLight

class TestSimulation:
    def __init__(self, gui,  max_step, green_duration, yellow_duration, input_dim, config_file, config_input):
        self._sumo_cmd = set_sumo(gui, config_file)
        # self._sumo_intersection = Routing(num_cars, max_step)
        self._input_dim = input_dim
        self._max_steps = max_step
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
        self._config_file = config_file
        self._config_input = config_input

        self._trafficlight_list = []
        self._num_actions = 0
        self._num_lanes = 0
    
    '''
    SUMO INTERACTIONS
    '''
    def run(self): #START SIMULATION
        # self._sumo_intersection.generate_routefile(episode)
        traci.start(self._sumo_cmd)

        if not self._trafficlight_list: #create model
            self.configure_model(
                self._config_input['input_dim'],
            )

        start_time = timeit.default_timer()
        getLogger().info('Simulating...')

        #init
        self._step = 0
        self._waiting_times = {}
        self._sum_reward = 0
        self._sum_queue_length = 0
        self._sum_waiting_time = 0            

        while self._step < self._max_steps:
            for tl in self._trafficlight_list:
                if traci.trafficlight.getNextSwitch(tl.id) - traci.simulation.getTime()  <= 0:
                    if self.isGreen(traci.trafficlight.getPhase(tl.id)):
                        current_state = self._get_state(tl.action, tl.lanes)
                        current_total_wait = self._get_waiting_time(tl.lanes)
                        tl.reward = tl.old_total_wait - current_total_wait
                
                        #traffic light phase
                        tl.action = self._choose_action(current_state, tl.agent)

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
                    
                queue_length = self._get_queue_length(tl.lanes)
                tl.sum_queue_length += queue_length
                tl.sum_waiting_time += queue_length

            traci.simulationStep()
            self._step += 1     

        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        for tl in self._trafficlight_list:
            #Save episode stats
            tl.save_stats(self._max_steps)
            getLogger().info(f'Queue Length: {round(tl.sum_queue_length / self._max_steps, 2)} Sum Waiting Time: {tl.sum_waiting_time}  Total nagative reward: {tl.sum_reward}')
            tl.reset_data()

        return simulation_time
    
    def _get_state(self, action, lanes): #GET STATE FROM SUMO
        #init
        position_matrix = np.zeros((self._num_lanes, self._input_dim))
        velocity_matrix = np.zeros((self._num_lanes, self._input_dim))
        phase_matrix = np.zeros(4)
        cell_length = 7

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
                    index_1 = index
                    index_2 = int((lane_length - lane_pos) / cell_length)

                    position_matrix[index_1][index_2] = 1
                    velocity_matrix[index_1][index_2] = speed

        # getLogger().info(f'Pos: {position_matrix} \n Vel: {velocity_matrix} \n Phase: {phase_matrix}')
        return [position_matrix, velocity_matrix, phase_matrix]        
    
    def _choose_action(self, state, agent):
        action = np.argmax(agent.predict_one(state))
        return action

    '''
    AGENT MODEL
    '''
    def configure_model(self, input_dim):
        traffic_lights = traci.trafficlight.getIDList()
        getLogger().info(f'Number of traffic lights detected: {len(traffic_lights)} ID: {traffic_lights}')

        for tl in traffic_lights:
            lanes = self._get_controlled_lanes(tl)
            phases = traci.trafficlight.getAllProgramLogics(tl)

            self._num_lanes = len(lanes)
            self._num_actions = int(len(phases[0].getPhases()) / 2)

            id = f'model_{input_dim}.{self._num_lanes}.{self._num_actions}'
            model_path, plot_path = get_model_path(self._config_input['model_folder'])
            os.path.join(model_path, id)
            agent = TestAgent(input_dim, self._num_lanes, model_path)
            self._trafficlight_list.append(TrafficLight(tl, lanes, agent))

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
        