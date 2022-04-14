from agent import Agent
from simulation import Simulation
from logger import Logger

if __name__ == "__main__":
    logger = Logger(__name__, 'debug.log') #(name, file name)
    
    logger.log_info('===== START PROGRAM =====')
    sample_agent = Agent()
    test_simulation = Simulation()
    
    test_simulation.run()
    logger.log_info('====== END PROGRAM ======')
