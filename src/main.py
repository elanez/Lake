import datetime

from agent import Agent
from simulation import Simulation
from logger import getLogger

if __name__ == "__main__":
    getLogger().info('===== START PROGRAM =====')
    sample_agent = Agent()
    test_simulation = Simulation(sample_agent) #(Agent())
    
    episode = 0
    total_episodes = 10
    timestamp_start = datetime.datetime.now()

    while episode < total_episodes:
        getLogger().info(f'Episode {episode+1} of {total_episodes}:')
        epsilon = 1 - (episode / total_episodes) #epsilon-greedy policy
        simulation_time, training_time = test_simulation.run(episode, epsilon)
        getLogger().info(f'Simulation time: {simulation_time} - Training time: {training_time} - Total: {round(simulation_time+training_time, 1)}')
        episode += 1
    
    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')

    getLogger().info('====== END PROGRAM ======')
