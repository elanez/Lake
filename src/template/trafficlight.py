class TrafficLight:
    def __init__(self, id, lanes, agent):
        self.id = id
        self.lanes = lanes
        self.agent = agent
        self.action = 0
        self.old_action = -1
        self.old_state = -1
        self.old_total_wait = 0
        self.reward = 0

    def reset_data(self):
        self.action = 0
        self.old_action = -1
        self.old_state = -1
        self.reward = 0
        
