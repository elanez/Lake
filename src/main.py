from agent import Agent
from simulation import Simulation
from logger import getLogger

if __name__ == "__main__":
    getLogger().info('===== START PROGRAM =====')
    sample_agent = Agent()
    test_simulation = Simulation()
    
    test_simulation.run()
    getLogger().info('====== END PROGRAM ======')
