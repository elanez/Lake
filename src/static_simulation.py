import os
import sys
import traci
import timeit
import datetime

from plot import Plot
from logger import getLogger
from tools import get_trafficlightID, set_sumo, get_num_lanes, get_model_path, import_test_config, get_path
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
            agent = None
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
                if traci.trafficlight.getNextSwitch(tl.id) - traci.simulation.getTime()  <= 0: # If trafficlight duration reaches zero
                    if self.isGreen(traci.trafficlight.getRedYellowGreenState(tl.id)): #GREEN PHASE
                        
                        current_total_wait = self._get_waiting_time(tl.lanes)
                        
                        #calculate reward
                        cars_passed = self._get_car_passtrough(tl.car_present, self._get_cars_in_lane(tl.lanes))
                        tl.car_present = self._get_cars_in_lane(tl.lanes)
                        queue_length = self._get_queue_length(tl.lanes)
                        if queue_length != 0:
                            plus_reward = cars_passed / queue_length
                        else:
                            plus_reward = cars_passed
                        tl.reward = tl.old_total_wait - current_total_wait + (plus_reward * (self._green_duration + self._yellow_duration))
                        
                        #traffic light phase
                        tl.action = self._choose_action(tl)
                        tl.action_store.append(tl.action)

                        #different phase
                        if self._step != 0 and tl.old_action != tl.action:
                            self._set_yellow_phase(tl)
                        else:
                            self._set_green_phase(tl)

                        tl.old_action = tl.action
                        tl.old_total_wait = current_total_wait

                        if tl.reward < 0:
                            tl.sum_reward += tl.reward
                    else: #YELLOW PHASE
                        self._set_green_phase(tl)
                    
                queue_length = self._get_queue_length(tl.lanes)
                tl.sum_queue_length += queue_length
                tl.sum_waiting_time += queue_length

            self._save_vehicle_stats()
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
    
    def _choose_action(self, tl):
        if tl.old_action + 1 >= tl.action_dim:
            return 0
        else:
            return tl.old_action + 1
        
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

def save_data(path, data, filename):
        with open(os.path.join(path,  f'test_{filename}_data.txt'), "w") as file:
            for value in data:
                    file.write("%s\n" % value)

if __name__ == "__main__":
    getLogger().info('===== START STATIC PROGRAM =====')
    config = import_test_config('test_settings.ini')

    simulation = TestSimulation(config)
    timestamp_start = datetime.datetime.now()
    simulation.run()
    
    #plot data
    model_path = get_model_path(config['model_folder'])
    plot = Plot(model_path, 90)
    wait_time, distance = simulation.get_vehicle_stats()
    # plot.scatter_plot(distance, wait_time, 'Vehicle_data', 'Distance', 'Wait Time')

    #init
    wait_time = {}
    ave_queue = {}

    for tl in simulation.traffic_light_list: #save model and plot data
        plot_path = get_path(model_path, tl.id)
        wait_time[tl.id] = tl.cumulative_wait_store[0]
        ave_queue[tl.id] = tl.avg_queue_length_store[0]
        save_data(plot_path, tl.cumulative_wait_store, 'Cumulative waiting time-Static')
        save_data(plot_path, tl.avg_queue_length_store, 'Avg Queue Length-Static')
        save_data(plot_path, tl.action_store, 'Actions-Static')
    
    plot.bar_graph(wait_time, 'static_waiting_time', 'Traffic light ID', 'Cumulative Wait Time')
    plot.bar_graph(ave_queue, 'static_ave_queue', 'Traffic light ID', 'Ave Queue length')
