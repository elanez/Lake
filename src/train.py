import datetime
import os

from shutil import copyfile

from agent import Agent
from train_simulation import TrainSimulation
from logger import getLogger
from config import import_train_config, set_model_path, training_data_path
from plot import Plot

if __name__ == "__main__":
    getLogger().info('===== START PROGRAM =====')
    config = import_train_config('train_settings.ini')
    path = set_model_path(config['model_folder'])

    agent = Agent(
        config['input_dim'],
        config['output_dim'],
        config['batch_size'],
        config['learning_rate'],
        config['num_lanes'],
        config['size_min'],
        config['size_max']
    )

    simulation = TrainSimulation(
        agent,
        config['sumo_gui'],
        config['epochs'],
        config['gamma'],
        config['max_step'],
        config['green_duration'],
        config['yellow_duration'],
        config['input_dim'],
        config['num_cars'],
        config['sumocfg_file']
    )

    plot = Plot(
        path,
        100
    )

    train_plot = Plot(
        training_data_path(path),
        100
    )
    
    episode = 0
    total_episodes = config['total_episodes']
    timestamp_start = datetime.datetime.now()

    while episode < total_episodes:
        getLogger().info(f'Episode {episode+1} of {total_episodes}:')
        epsilon = 1 - (episode / total_episodes) #epsilon-greedy policy
        simulation_time, training_time = simulation.run(episode, epsilon)
        
        if agent.loss_history and agent.acc_history and episode > int(total_episodes*9/10):
            train_plot.plot_data(data=agent.loss_history,  filename=f'Loss_Episode_{episode+1}', xlabel='Epoch', ylabel='Loss')
            train_plot.plot_data(data=agent.acc_history,  filename=f'Acc_Episode_{episode+1}', xlabel='Accuracy', ylabel='Loss')

        getLogger().info(f'Simulation time: {simulation_time} - Training time: {training_time} - Total: {round(simulation_time+training_time, 1)}')
        episode += 1
    
    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')

    agent.save_model(path)
    copyfile(src='train_settings.ini', dst=os.path.join(path, 'train_settings.ini'))

    getLogger().info('====== END PROGRAM ======')

    #save reward store to plot data
    plot.plot_data(data=simulation.reward_store, filename='reward', xlabel='Episode', ylabel='Cumulative negative reward')
    plot.plot_data(data=simulation.cumulative_wait_store, filename='delay', xlabel='Episode', ylabel='Cumulative delay (s)')
    plot.plot_data(data=simulation.avg_queue_length_store, filename='queue', xlabel='Episode', ylabel='Average queue length (vehicles)')