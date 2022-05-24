import traci
import timeit
import datetime
import numpy as np

from config import set_sumo
from logger import getLogger
from config import import_test_config

class StaticSimulation:
    def __init__(self, gui, max_step, green_duration, yellow_duration, config_file):
        self._sumo_cmd = set_sumo(gui, config_file)
        self._step = 0
        self._max_steps = max_step
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
    
         #stats
        self._reward_store = []
        self._cumulative_wait_store = []
        self._queue_length = []
        self._wait_store = []
        self._min_wait_time = 100
        self._max_wait_time = 0
    
    def run(self):
        start_time = timeit.default_timer()
        traci.start(self._sumo_cmd)
        getLogger().info('Simulating...')

        self._step = 0
        self._waiting_times = {}
        trafficlight_list = traci.trafficlight.getIDList()
        trafficlight_count = len(trafficlight_list)
        old_total_wait = np.zeros(trafficlight_count)
        action = np.zeros(trafficlight_count)
        old_action = np.zeros(trafficlight_count)
        reward = np.zeros(trafficlight_count)
        ave_wait_time = 0

        while self._step < self._max_steps:
            for index, trafficlight_id in enumerate(trafficlight_list):
                if self.isGreen(traci.trafficlight.getPhase(trafficlight_id)):
                    current_total_wait, ave_wait_time = self._get_waiting_time(trafficlight_id)
                    reward[index] = old_total_wait[index] - current_total_wait
                    
                    if ave_wait_time > 0:
                        self._wait_store.append(ave_wait_time)

                    old_action[index]  = action[index] 
                    old_total_wait[index] = current_total_wait

                    self._reward_store.append(reward[index])
                    queue_length = self._get_queue_length(trafficlight_id)
                    self._queue_length.append(queue_length)

            traci.simulationStep()
            self._step += 1

        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time
    
    def _get_waiting_time(self, trafficlight_id): #GET ALL WAITING TIME FOR ALL INCOMING LANES
        car_list = traci.vehicle.getIDList()
        wait_time_store = []
        ave_wait_time = 0

        lanes = self._get_controlled_lanes(trafficlight_id)
        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getLaneID(car_id)        
            if road_id in lanes:
                self._waiting_times[car_id] = wait_time
                
                if wait_time > self._max_wait_time:
                    self._max_wait_time = wait_time
                elif wait_time < self._min_wait_time and wait_time > 0:
                    self._min_wait_time = wait_time

                wait_time_store.append(wait_time)
            else:
                if car_id in self._waiting_times: #if car has left the intersection
                    del self._waiting_times[car_id]
        
        total_waiting_time = sum(self._waiting_times.values())

        if wait_time_store:
            ave_wait_time = sum(wait_time_store) / len(wait_time_store)

        return total_waiting_time, ave_wait_time
    
    def _get_queue_length(self, trafficlight_id): #GET QUEUE LENGTH FOR ALL INCOMING LANES
        queue_length = 0

        lanes = self._get_controlled_lanes(trafficlight_id)
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

if __name__ == "__main__":
    getLogger().info('===== START STATIC SIMULATION =====')
    config = import_test_config('test_settings.ini')

    simulation = StaticSimulation(
        config['sumo_gui'],
        config['max_step'],
        config['green_duration'],
        config['yellow_duration'],
        config['sumocfg_file']
    )
    simulation.run()

    timestamp_start = datetime.datetime.now()

    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')
    getLogger().info(f'RESULT -> Ave Queue Length: {simulation.average_queue_length()} Ave Wait Time: {simulation.average_waiting_time()}')

    getLogger().info('====== END STATIC SIMULATION ======')
