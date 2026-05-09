import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import PPO

# 1. Map your text gestures to numbers for the AI
# In BOTH files, use the same mapping:
GESTURE_MAP = {
    'NONE': 0,
    'FORWARD': 1,
    'BACK': 2,
    'JUMP': 3,
    'ATTACK': 4,
    'SHIELD': 5,
}
ACTION_MAP = {0: "IDLE", 1: "ATTACK", 2: "SHIELD", 3: "JUMP", 4: "FORWARD", 5: "BACKWARD"}
class BossAIEnv(gym.Env):
    def __init__(self):
        super().__init__()
        # Ensure shape matches your state array
        self.observation_space = spaces.Box(low=0, high=1, shape=(4,), dtype=np.float32)
        self.action_space = spaces.Discrete(6)

    def reset(self, seed=None):
        super().reset(seed=seed)
        # MUST return 4 values to match shape=(4,)
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32), {}

    def step(self, action):  # <--- Double check this name and indentation!
        human_gesture = np.random.choice([0, 4], p=[0.7, 0.3])
        
        reward = 0
        if human_gesture == 4:  # Human attacks
            reward = 10 if action == 2 else -10 # Reward Shield
        else:                   # Human idle
            reward = 10 if action == 1 else 2   # Reward Attack

        state = np.array([human_gesture / 5.0, 0.0, 0.0, 1.0], dtype=np.float32)
        
        # In Gymnasium, you must return 5 values
        return state, float(reward), False, False, {}
# 2. Train the AI
env = BossAIEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=50000)

# 3. Save the "Brain" to use in your game
model.save("boss_reaction_model")