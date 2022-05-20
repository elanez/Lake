import datetime
import os

from shutil import copyfile

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
        config['num_cars'],
        config['sumocfg_file']
    )

    timestamp_start = datetime.datetime.now()
    simulation.run(config['episode_seed'])
    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')
    getLogger().info(f'RESULT -> Ave Queue Length: {simulation.average_queue_length()}')
    # copyfile(src='test_settings.ini', dst=os.path.join(model_path, 'test_settings.ini'))

    getLogger().info('====== END TEST PROGRAM ======')

