import traci
import timeit
import numpy as np

from config import set_sumo
from logger import getLogger
from routing import Routing

#PHASE CODE from SUMO
PHASE_EW_GREEN = 0
PHASE_EW_YELLOW = 1
PHASE_EWS_GREEN = 2
PHASE_EWS_YELLOW = 3
PHASE_NS_GREEN = 4
PHASE_NS_YELLOW = 5
PHASE_NSS_GREEN = 6
PHASE_NSS_YELLOW = 7

class TestSimulation():
    def __init__(self, AGENT, gui, max_step, green_duration, yellow_duration, input_dim, num_cars, config_file):
        self._AGENT = AGENT
        self._sumo_cmd = set_sumo(gui, config_file)
        self._sumo_intersection = Routing(num_cars, max_step)
        self._input_dim = input_dim
        self._num_actions = 4
        self._step = 0
        self._max_steps = max_step
        self._green_duration = green_duration
        self._yellow_duraiton = yellow_duration

        self._reward_episode = []
        self._queue_length_episode = []
    
    def run(self, episode):
        start_time = timeit.default_timer()

        self._sumo_intersection.generate_routefile(episode)
        traci.start(self._sumo_cmd)
        getLogger().info('Simulating...')

        #init
        self._step = 0
        self._waiting_times = {}
        old_total_wait = 0
        old_action = -1
        action = 0

        while self._step < self._max_steps:
            current_state = self._get_state(action)
            # getLogger().info(f'Current State: {current_state}')

            current_total_wait = self._get_waiting_time()
            reward = old_total_wait - current_total_wait

            #traffic light phase
            action = self._choose_action(current_state)

            #different phase
            if self._step != 0 and old_action != action:
                self._set_yellow_phase(old_action)
                self._simulate(self._yellow_duraiton)
            
            self._set_green_phase(action)
            self._simulate(self._green_duration)

            old_action = action
            old_total_wait = current_total_wait

            self._reward_episode.append(reward)
        
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time
    
    def _get_state(self, action): #GET STATE FROM SUMO
        #init
        position_matrix = np.zeros((self._input_dim, 16))
        velocity_matrix = np.zeros((self._input_dim, 16))
        phase_matrix = np.zeros(4)
        cell_length = 7
        offset = 1

        #phase matrix based on current active traffic light phase
        if action < 4:
            phase_matrix[action] = 1
        else:
            getLogger().debug(f'Incorrect Green phase action: {action} from getState()')

        traffic_lights = traci.trafficlight.getIDList()

        for tl in traffic_lights:
            lanes = self._get_controlled_lanes(tl)

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

        return [position_matrix, velocity_matrix, phase_matrix]

    def _simulate(self, steps_todo): #RUN SUMO SIMULATION
        if (self._step + steps_todo) >= self._max_steps: 
            steps_todo = self._max_steps - self._step
        
        while steps_todo > 0:
            traci.simulationStep()  # simulate 1 step in sumo
            self._step += 1
            steps_todo -= 1
            queue_length = self._get_queue_length()
            self._queue_length_episode.append(queue_length)
    
    def _choose_action(self, state): #CHOOSE ACTION
        action = np.argmax(self._AGENT.predict_one(state))
        # getLogger().info(f'Action: {action}')
        return action

    '''
    UTILS
    '''  
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
        traffic_lights = traci.trafficlight.getIDList()
        car_list = traci.vehicle.getIDList()

        for tl in traffic_lights:
            lanes = self._get_controlled_lanes(tl)
            for car_id in car_list:
                wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
                road_id = traci.vehicle.getRoadID(car_id)        
                if road_id in lanes:
                    self._waiting_times[car_id] = wait_time
                else:
                    if car_id in self._waiting_times: #if car has left the intersection
                        del self._waiting_times[car_id]
        
        total_waiting_time = sum(self._waiting_times.values())
        return total_waiting_time
    
    def _get_queue_length(self): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        traffic_lights = traci.trafficlight.getIDList()
        queue_length = 0

        for tl in traffic_lights:
            lanes = self._get_controlled_lanes(tl)
            for l in lanes:
                queue_length = queue_length + traci.lane.getLastStepHaltingNumber(l)

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