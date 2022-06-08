import os
import datetime

from logger import getLogger
from test_simulation import TestSimulation
from tools import import_test_config

if __name__ == "__main__":
    getLogger().info('===== START TEST PROGRAM =====')
    config = import_test_config('test_settings.ini')
    model_path = os.path.join(os.getcwd(), 'models')

    simulation = TestSimulation(config)
    timestamp_start = datetime.datetime.now()
    simulation.run()

    '''
    #plot data
    model_path = get_model_path(config['model_folder'])
    plot = Plot(model_path, 90)
    wait_time, distance = simulation.get_vehicle_stats()
    plot.scatter_plot(distance, wait_time, 'Vehicle_data', 'Distance', 'Wait Time')

    #init
    wait_time = {}
    ave_queue = {}

    for tl in simulation.traffic_light_list: #save model and plot data
        plot_path = get_path(model_path, tl.id)
        wait_time[tl.id] = tl.cumulative_wait_store[0]
        ave_queue[tl.id] = tl.avg_queue_length_store[0]
        # tl.agent.save_data(plot_path, tl.cumulative_wait_store, 'Cumulative waiting time')
        # tl.agent.save_data(plot_path, tl.avg_queue_length_store, 'Avg Queue Length')
        # tl.agent.save_data(plot_path, tl.action_store, 'Actions')
    
    plot.bar_graph(wait_time, 'Waiting_Time', 'Traffic light ID', 'Cumulative Wait Time')
    plot.bar_graph(ave_queue, 'Ave_Queue', 'Traffic light ID', 'Ave Queue length')

    '''

    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')
    # getLogger().info(f'Average wait time: {sum(wait_time)/len(wait_time)}')
    getLogger().info('====== END TEST PROGRAM ======')

