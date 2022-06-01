class TrafficLight:
    def __init__(self, id, agent):
        self.id = id
        self.agent = agent
        self.reset_data()
        self.lanes = None

        #STATS
        self.reward_store = []
        self.cumulative_wait_store = []
        self.avg_queue_length_store = []

    def reset_data(self):
        self.action = 0
        self.old_action = 0
        self.old_state = -1
        self.old_total_wait = 0
        self.reward = 0
        self.sum_reward = 0
        self.sum_waiting_time = 0
        self.sum_queue_length = 0
    
    def save_stats(self, max_step):
        self.reward_store.append(self.sum_reward)
        self.cumulative_wait_store.append(self.sum_waiting_time)
        self.avg_queue_length_store.append(self.sum_queue_length / max_step)
        
