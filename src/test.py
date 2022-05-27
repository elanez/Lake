import os
import datetime

from plot import Plot
from agent import TestAgent
from test_simulation import TestSimulation
from logger import getLogger
from config import import_test_config, get_model_path

if __name__ == "__main__":
    getLogger().info('===== START TEST PROGRAM =====')
    config = import_test_config('test_settings.ini')
    model_path,plot_path = get_model_path(config['model_folder'])

    agent = TestAgent(
        config['input_dim'],
        config['num_lanes'],
        model_path
    )

    simulation = TestSimulation(
        agent,
        config['sumo_gui'],
        config['max_step'],
        config['green_duration'],
        config['yellow_duration'],
        config['input_dim'],
        config['sumocfg_file']
    )

    plot = Plot(
        plot_path,
        100
    )

    timestamp_start = datetime.datetime.now()
    simulation.run()
    distance, wait_time = simulation.get_stats()

    plot.scatter_plot(distance, wait_time, 'model_test', 'Distance Travelled', 'Waiting Time')

    ave_wait_time = round(sum(wait_time)/len(wait_time), 2)
    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')
    getLogger().info(f'RESULT -> Ave Queue Length: {simulation.average_queue_length()} Ave Waiting Time: {ave_wait_time}')

    getLogger().info('====== END TEST PROGRAM ======')

