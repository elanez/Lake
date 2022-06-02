import os
import traci
import timeit
import datetime
import numpy as np

from plot import Plot
from tools import set_sumo
from logger import getLogger
from tools import import_test_config

class StaticSimulation:
    def __init__(self, gui, max_step, green_duration, yellow_duration, config_file):
        self._sumo_cmd = set_sumo(gui, config_file)
        self._step = 0
        self._max_steps = max_step
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
    
        #stats
        self._reward_store = []
        self._wait_store = {}
        self._distance_store = {}
        self._queue_length = []
    
    # def configure_model(self):
    #     self._trafficlight_list = []
    #     path = os.path.join('sumo_files', f'{net_file}.net.xml')
    #     net = sumolib.net.readNet(path)
    #     traffic_lights = net.getTrafficLights()
    #     for tl in traffic_lights:
    #         self._trafficlight_list.append(TrafficLight(tl.getID(),num_lanes,None))

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

        while self._step < self._max_steps:
            for index, trafficlight_id in enumerate(trafficlight_list):
                if self._step == 0:
                    logic = traci.trafficlight.getAllProgramLogics(trafficlight_id)
                    phase = logic[0].getPhases()
                    print(phase[0].state)
                    traci.trafficlight.setRedYellowGreenState(trafficlight_id, 'rrrrrrrrrrrrrrrrrrrrrrrr')
                    traci.trafficlight.setPhaseDuration(trafficlight_id, 3)
                    # ryg = traci.trafficlight.getRedYellowGreenState(trafficlight_id)
                    # print(ryg)
                if self.isGreen(traci.trafficlight.getPhase(trafficlight_id)):
                    current_total_wait = self._get_waiting_time(trafficlight_id)
                    reward[index] = old_total_wait[index] - current_total_wait

                    old_action[index]  = action[index] 
                    old_total_wait[index] = current_total_wait

                    self._reward_store.append(reward[index])
                    queue_length = self._get_queue_length(trafficlight_id)
                    self._queue_length.append(queue_length)
                # print(traci.trafficlight.getNextSwitch(trafficlight_id) - traci.simulation.getTime())
            self._save_stats()
            traci.simulationStep()
            self._step += 1

        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time
    
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

if __name__ == "__main__":
    getLogger().info('===== START STATIC SIMULATION =====')
    config = import_test_config('test_settings.ini')
    # model_path, plot_path = get_path(config['model_folder'])

    simulation = StaticSimulation(
        False,
        config['max_step'],
        config['green_duration'],
        config['yellow_duration'],
        config['sumocfg_file']
    )

    # plot = Plot(
    #     plot_path,
    #     100
    # )

    simulation.run()
    timestamp_start = datetime.datetime.now()
    y, x = simulation.get_stats()

    # plot.scatter_plot(x, y, 'static_test', 'Distance Travelled', 'Waiting Time')

    ave_wait_time = round(sum(y)/len(y), 2)
    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')
    getLogger().info(f'RESULT -> Ave Queue Length: {simulation.average_queue_length()} Ave Waiting Time: {ave_wait_time}')

    getLogger().info('====== END STATIC SIMULATION ======')

