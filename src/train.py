import datetime
import os

from shutil import copyfile

from train_simulation import TrainSimulation
from logger import getLogger
from config import import_train_config, set_model_path, set_path
from plot import Plot

if __name__ == "__main__":
    getLogger().info('===== START TRAIN PROGRAM =====')
    config = import_train_config('train_settings.ini')
    
    simulation = TrainSimulation(
        config['sumo_gui'],
        config['epochs'],
        config['gamma'],
        config['max_step'],
        config['green_duration'],
        config['yellow_duration'],
        config['input_dim'],
        config['num_cars'],
        config['sumocfg_file'],
        config
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
    
    model_path = set_model_path(config['model_folder'])
    for tl in simulation.traffic_light_list: #save model and plot data
        tl.agent.save_model(model_path)
        plot_path = set_path(config['model_folder'], tl.agent.id)
        tl.agent.plot_data(plot_path, 100, tl)

    # copyfile(src='train_settings.ini', dst=os.path.join(path, 'train_settings.ini'))

    getLogger().info('====== END TRAIN PROGRAM ======')
