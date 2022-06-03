import os
import datetime

from matplotlib.pyplot import scatter

from plot import Plot
from logger import getLogger
from test_simulation import TestSimulation
from tools import get_model_path, import_test_config

if __name__ == "__main__":
    getLogger().info('===== START TEST PROGRAM =====')
    config = import_test_config('test_settings.ini')
    model_path = os.path.join(os.getcwd(), 'models')

    simulation = TestSimulation(config)
    timestamp_start = datetime.datetime.now()
    simulation.run()

    #plot data
    model_path = get_model_path(config['model_folder'])
    scatter = Plot(model_path, 90)
    wait_time, distance = simulation.get_vehicle_stats()
    scatter.scatter_plot(distance, wait_time, 'vehicle_data', 'Distance', 'Wait Time')

    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')
    getLogger().info(f'Average wait time: {sum(wait_time)/len(wait_time)}')
    getLogger().info('====== END TEST PROGRAM ======')

