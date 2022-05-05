import datetime
import os

from agent import TestAgent
from test_simulation import TestSimulation
from logger import getLogger
from config import import_test_config, set_model_path

if __name__ == "__main__":
    getLogger().info('===== START PROGRAM =====')
    config = import_test_config('test_config.ini')
    path = set_model_path(config['model_name'])

    agent = TestAgent(
        config['input_dim'],
        'models/model.h5'
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
    getLogger().info('====== END PROGRAM ======')

