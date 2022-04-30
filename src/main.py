import datetime

from agent import Agent
from simulation import Simulation
from logger import getLogger
from config import import_configuration, set_model_path

if __name__ == "__main__":
    getLogger().info('===== START PROGRAM =====')
    config = import_configuration('settings.ini')

    agent = Agent(
        config['input_dim'],
        config['output_dim'],
        config['batch_size'],
        config['learning_rate'],
        config['size_min'],
        config['size_max']
    )

    simulation = Simulation(
        agent,
        config['sumo_gui'],
        config['epochs'],
        config['gamma'],
        config['max_step'],
        config['input_dim'],
        config['num_cars'],
        config['sumocfg_file']
    )
    
    episode = 0
    total_episodes = config['total_episodes']
    timestamp_start = datetime.datetime.now()

    while episode < total_episodes:
        getLogger().info(f'Episode {episode+1} of {total_episodes}:')
        epsilon = 1 - (episode / total_episodes) #epsilon-greedy policy
        simulation_time, training_time = simulation.run(episode, epsilon)
        getLogger().info(f'Simulation time: {simulation_time} - Training time: {training_time} - Total: {round(simulation_time+training_time, 1)}')
        episode += 1
    
    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')

    agent.save_model(set_model_path(config['model_name']))

    getLogger().info('====== END PROGRAM ======')
