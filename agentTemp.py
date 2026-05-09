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
        # Match what you actually return: just gesture (0-5)
        self.observation_space = spaces.Box(low=0, high=1, shape=(3,), dtype=np.float32)
        self.action_space = spaces.Discrete(6)

    def reset(self, seed=None):
        super().reset(seed=seed)
        # Initialize variables here so they reset every game
        self.boss_health = 100
        self.last_action = 0
        self.consecutive_attacks = 0
        self.last_human_gesture = 0
        
        # Initial observation
        return np.array([0.0, 1.0, 0.0], dtype=np.float32), {}
    
    def step(self, action):

        human_gesture = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.3, 0.1, 0.1, 0.1, 0.3, 0.1])
        # Track state across steps
        if not hasattr(self, 'boss_health'):
            self.boss_health = 100
            self.last_action = 0
            self.consecutive_attacks = 0
            self.last_human_gesture = 0

        reward = 0

        if human_gesture == 0:  # Human idle
            if action == 1:  # Boss attacks idle human = good
                reward += 20
            elif action == 4:  # Boss moves forward to pressure
                reward += 10
            else:
                reward -= 10  # Missed opportunity

        if human_gesture == 4:  # Human attacking
            if action == 2:  # Boss shields successfully
                reward += 25
            elif action == 1 or action == 4:  # Boss tries to attack into human attack = bad
                reward -= 10
            elif action == 5:  # Boss back away from attack = smart
                reward += 15
            else:
                reward -= 15  # Didn't react properly

        if human_gesture == 5:  # Human shielding
            if action == 1:  # Boss attacking into shield = bad
                reward -= 20
            elif action == 2:  # Boss also shields = stalemate
                reward += 5
            elif action == 4:  # Boss moves forward to pressure shield = good
                reward += 10
            else:  # Boss does something else = punish
                reward -= 5

        if human_gesture == 3:  # Human jumps
            if getattr(self, 'last_human_gesture', 0) == 1:  # Human moved forward then jumped
                if action in [2, 5]:  # Boss shields or moves backward
                    reward += 20
                else:
                    reward -= 15
            else:
                if action == 1:  # Boss attacks jump = good
                    reward += 20
                elif action == 2:  # Boss shields jump = bad (wasted)
                    reward -= 10
                elif action == 4:  # Boss moves forward to pressure jump = risky but good
                    reward += 5
                else:
                    reward -= 5  # Didn't react to jump



        # COUNTER-ATTACK WINDOW: Reward attacking right after defending
        if self.last_action == 2 and action == 1:  # Shield → Attack
            reward += 15  # Punish cooldown, force aggression

        # COMBO PRESSURE: Human attacking repeatedly
        if human_gesture == 4:
            self.consecutive_attacks += 1
            if self.consecutive_attacks > 2:  # 3+ attacks = get aggressive
                if action == 1:  # Boss counter-attacks
                    reward += 30
                elif action == 2:
                    reward -= 10  # Don't just shield forever
            else:
                if action in [2,5]:  # Shield or back away
                    reward +=20
                else:
                    reward -=25
        else:
            self.consecutive_attacks = 0

        if human_gesture == 5:  # Human shielding
            if action == 1:  # Boss attacking into shield = bad
                reward -= 20
            elif action == 2:  # Boss also shields = stalemate
                reward += 5
            else:  # Boss does something else = punish
                reward -= 15
                
        # HEALTH-BASED AGGRESSION: Low health = more desperate
        if self.boss_health < 25:  # Desperation mode
            if action == 1:  # Attack less
                reward -= 25
            elif action == 2 or action == 5:  # Shield
                reward += 10
        elif self.boss_health > 75:  # Winning = be aggressive
            if action == 1:
                reward += 15
            elif action == 5:  # Don't run away
                reward -= 10

        # DISTANCE MANAGEMENT: Close distance to attack
        if human_gesture == 4:  # Human attacking
            if action == 4:  # Back away (create space)
                reward += 18
        elif human_gesture == 0:  # Human idle = rush in
            if action == 1:  # Dash attack
                reward += 22
            if action == 4:  # forward attack
                reward += 12

        # Simulate taking damage
        if human_gesture == 4 and action != 2:  # Got hit
            self.boss_health -= 5

        # Take damage when shielding too much (stamina break)
        if self.last_action == 2 and action == 2:  # Holding shield
            self.boss_health -= 1

        self.last_action = action
        self.last_human_gesture = human_gesture
        state = np.array([
            human_gesture / 5.0,        # Scaled 0.0 to 1.0
            self.boss_health / 100.0,   # Scaled 0.0 to 1.0
            self.consecutive_attacks / 5.0  # Scaled 0.0 to 1.0
        ], dtype=np.float32)
        done = self.boss_health <= 0
        return state, reward, done, False, {}

# 2. Train the AI
env = BossAIEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=50000)

# 3. Save the "Brain" to use in your game
model.save("boss_reaction_model")