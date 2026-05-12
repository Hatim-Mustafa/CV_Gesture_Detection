import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import PPO

def inRange(player_coords, boss_coords, threshold=200.0):
    px, py = player_coords
    bx, by = boss_coords
    distance = np.sqrt((px - bx)**2 + (py - by)**2)
    return distance <= threshold, distance

def is_human_on_left(player_coords, boss_coords):
    px, py = player_coords
    bx, by = boss_coords
    return px < bx

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
        # Observation: [human_gesture, boss_health, consecutive_attacks, is_in_range, is_human_on_left]
        self.observation_space = spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32)
        self.action_space = spaces.Discrete(6)
        self.current_step = 0

    def reset(self, seed=None):
        super().reset(seed=seed)
        # Randomize health for training so it learns behavior at all health levels
        self.boss_health = np.random.randint(1, 101) 
        self.last_action = 0
        self.consecutive_attacks = 0
        self.current_step = 0
        
        # Start with a random human gesture and store it so the AI knows what to react to
        self.current_human_gesture = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.3, 0.1, 0.1, 0.1, 0.3, 0.1])
        self.last_human_gesture = self.current_human_gesture
        
        # Generate random coordinates for this frame (1400x350 to match new screen bounds)
        px, py = np.random.uniform(0, 1400), np.random.uniform(0, 350)
        bx, by = np.random.uniform(0, 1400), np.random.uniform(0, 350)
        self.is_in_range, distance = inRange((px, py), (bx, by), threshold=200.0)
        self.human_is_left = is_human_on_left((px, py), (bx, by))

        # Initial observation
        return np.array([self.current_human_gesture / 5.0, self.boss_health / 100.0, 0.0, float(self.is_in_range), float(self.human_is_left)], dtype=np.float32), {}
    
    def step(self, action):
        self.current_step += 1
        # Randomize health every step to decouple it from previous actions
        self.boss_health = np.random.randint(1, 101)

        # AI reacts to current_human_gesture
        human_gesture = self.current_human_gesture
        
        # Track state across steps
        if not hasattr(self, 'last_action'):
            self.last_action = 0
            self.consecutive_attacks = 0
            self.last_human_gesture = 0

        # Generate fresh random coordinates (1400x350)
        px, py = np.random.uniform(0, 1400), np.random.uniform(0, 350)
        bx, by = np.random.uniform(0, 1400), np.random.uniform(0, 350)
        self.is_in_range, distance = inRange((px, py), (bx, by), threshold=200.0)
        self.human_is_left = is_human_on_left((px, py), (bx, by))

        reward = 0

        if self.human_is_left:
            if self.is_in_range:
                if human_gesture == 0: # Human idle and in range -> Pressure them
                    if action == 1:  # attack if in range
                        reward += 30
                    else:
                        reward -= 20
                
                if human_gesture == 1:
                    if getattr(self, 'last_human_gesture', 0) == 3:
                        if action in [2, 4]:  # Boss shields or moves backward from jump-then-forward
                            reward += 20

                    if action == 1:  # Boss attacks forward-moving human = good
                        reward += 15
                    elif action == 4:  # Boss moves forward to dodge forward movement = good
                        reward += 10
                    elif action == 5:  # Boss moves backward into forward movement = bad
                        reward -= 20
                    elif action == 2 or action == 3:  # potentially shielding forward movement = risky, could be good or bad
                        reward += 5
                    else:
                        reward -= 5  # Missed opportunity

                if human_gesture == 2:  # Human moving backward
                    if action == 1:  # Boss attacks retreating human = good
                        reward += 20
                    elif action == 5:  # Boss moves backward to close gap = good
                        reward += 10
                    elif action == 4:  # Boss moves forward into backward movement = bad
                        reward -= 5
                    elif action == 0 or action == 3 or action==2:  # potentially shielding backward movement = risky, could be good or bad
                        reward =reward  # Neutral

                if human_gesture ==3:  # Human jumps
                    if action == 4 or action == 5:  # Boss attacks jump = good
                        reward += 10
                    elif action == 2:  # Boss shields jump = bad (wasted)
                        reward += 5
                    elif action == 3:  # Boss jumps to meet jump = risky but good
                        reward += 2
                    elif action == 1: # Boss does something else = punish
                        reward -= 5
                
                if human_gesture==4: # Human attack and in range -> Run away or shield
                    self.consecutive_attacks += 1
                    if self.consecutive_attacks <= 2:
                        if action == 4 or action == 2 or action == 3: # FORWARD (Move Right to dodge) or BACKWARD (Move Left to dodge)
                            reward += 20
                        elif action == 5: # BACKWARD (Move Left into attack)
                            reward -= 10
                        else:
                            reward -= 30  # Missed opportunity to react to attack
                    else:
                        if action == 1:  # Boss counter-attacks
                            reward += 30
                        elif action == 2:
                            reward -= 10  # Don't just shield forever
                        elif action in [3,4]:  # Boss moves forward to pressure attack = risky but good
                            reward += 25
                        else:
                            reward -= 25  # Didn't react properly to repeated attacks
                
                if human_gesture == 5:  # Human shielding
                    if self.last_action == 3 and action==5:  # Jumping followed by moving backward(left)
                        reward += 30
                    elif action == 1:  # Boss attacking into shield = bad
                        reward -= 20
                    elif action == 3:
                        reward -= 10
                    elif action in [2,0]:  # Boss shields or stays still = stalemate
                        reward += 1
                    elif action == 5:  # Boss moves left to pressure shield = good
                        reward += 10

                if self.boss_health < 25:  # Desperation mode
                    if action == 1:  # Attack less
                        reward -= 25
                    elif action in [2, 4]:  # Shield or run away
                        reward += 15
                elif self.boss_health > 75:  # Winning = be aggressive
                    if action == 1:
                        reward += 10  
                    else:  # Don't run away
                        reward -= 5

            else:
                if action in [0,1,2,3]:  # Boss attacks from far away = bad
                    reward -= 10
                elif action == 5:  # Boss moves backward to close distance = good
                    reward += 20
                elif action == 4:  # Boss moves forward to stay far = bad
                    reward -= 20

                if self.last_action== 5 and action == 1:  # Closing distance then attacking
                    reward += 12  # Reward smart aggression after closing gap

                if self.last_action== 5 and action == 3: # Closing distance then jumping to meet them
                    reward += 15  
                if self.last_action== 3 and action == 5: # Jumping then closing distance
                    reward += 15

                if self.boss_health < 25:  # Desperation mode
                    if action == 4:  # Run away more
                        reward += 10
                    elif action == 5:  # Attack less
                        reward -= 10
                elif self.boss_health > 75:  # Winning = be aggressive
                    if action == 5:
                        reward += 15  
                    else :
                        reward -= 10

        else: # IF HUMAN ON RIGHT
            if self.is_in_range:
                if human_gesture == 0: # Human idle and in range -> Pressure them
                    if action == 1:  # attack if in range
                        reward += 30
                    else:
                        reward -= 20
                
                if human_gesture == 1:
                    if getattr(self, 'last_human_gesture', 0) == 3:
                        if action in [2, 5]:  # Boss shields or moves forward from jump-then-forward
                            reward += 20

                    if action == 1:  # Boss attacks forward-moving human = good
                        reward += 15
                    elif action == 5:  # Boss moves forward to dodge forward movement = good
                        reward += 10
                    elif action == 4:  # Boss moves backward into forward movement = bad
                        reward -= 20
                    elif action == 2 or action == 3:  # potentially shielding forward movement = risky, could be good or bad
                        reward += 5
                    else:
                        reward -= 5  # Missed opportunity

                if human_gesture == 2:  # Human moving backward
                    if action == 1:  # Boss attacks retreating human = good
                        reward += 20
                    elif action == 4:  # Boss moves backward to close gap = good
                        reward += 10
                    elif action == 5:  # Boss moves forward into backward movement = bad
                        reward -= 5
                    elif action == 0 or action == 3 or action==2:  # potentially shielding backward movement = risky, could be good or bad
                        reward =reward  # Neutral

                if human_gesture ==3:  # Human jumps
                    if action == 5 or action == 4:  # Boss attacks jump = good
                        reward += 10
                    elif action == 2:  # Boss shields jump = bad (wasted)
                        reward += 5
                    elif action == 3:  # Boss jumps to meet jump = risky but good
                        reward += 2
                    elif action == 1: # Boss does something else = punish
                        reward -= 5
                
                if human_gesture==4: # Human attack and in range -> Run away or shield
                    self.consecutive_attacks += 1
                    if self.consecutive_attacks <= 2:
                        if action == 5 or action == 2 or action == 3: # FORWARD (Move Right to dodge) or BACKWARD (Move Left to dodge)
                            reward += 20
                        elif action == 4: # BACKWARD (Move Left into attack)
                            reward -= 10
                        else:
                            reward -= 30  # Missed opportunity to react to attack
                    else:
                        if action == 1:  # Boss counter-attacks
                            reward += 30
                        elif action == 2:
                            reward -= 10  # Don't just shield forever
                        elif action in [3,5]:  # Boss moves forward to pressure attack = risky but good
                            reward += 25
                        else:
                            reward -= 25  # Didn't react properly to repeated attacks
                
                if human_gesture == 5:  # Human shielding
                    if self.last_action == 3 and action==4:  # Jumping followed by moving backward(left)
                        reward += 30
                    elif action == 1:  # Boss attacking into shield = bad
                        reward -= 20
                    elif action == 3:
                        reward -= 10
                    elif action in [2,0]:  # Boss shields or stays still = stalemate
                        reward += 1
                    elif action == 4:  # Boss moves left to pressure shield = good
                        reward += 10
                
                if self.boss_health < 25:  # Desperation mode
                    if action == 1:  # Attack less
                        reward -= 25
                    elif action in [2, 5]:  # Shield or run away
                        reward += 15
                elif self.boss_health > 75:  # Winning = be aggressive
                    if action == 1:
                        reward += 10  
                    else:  # Don't run away
                        reward -= 5

            else:
                if action in [0,1,2,3]:  # Boss attacks from far away = bad
                    reward -= 10
                elif action == 4:  # Boss moves backward to close distance = good
                    reward += 20
                elif action == 5:  # Boss moves forward to stay far = bad
                    reward -= 20

                if self.last_action== 4 and action == 1:  # Closing distance then attacking
                    reward += 12  # Reward smart aggression after closing gap

                if self.last_action== 4 and action == 3: # Closing distance then jumping to meet them
                    reward += 15  
                if self.last_action== 3 and action == 4: # Jumping then closing distance
                    reward += 15

                if self.boss_health < 25:  # Desperation mode
                    if action == 5:  # Run away more
                        reward += 10
                    elif action == 4:  # Attack less
                        reward -= 10
                elif self.boss_health > 75:  # Winning = be aggressive
                    if action == 4:
                        reward += 15  
                    else :
                        reward -= 10
    

        self.last_action = action
        self.last_human_gesture = self.current_human_gesture
        
        # Determine human gesture for the NEXT step
        self.current_human_gesture = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.3, 0.1, 0.1, 0.1, 0.3, 0.1])
        
        state = np.array([
            self.current_human_gesture / 5.0,        # Scaled 0.0 to 1.0
            self.boss_health / 100.0,   # Scaled 0.0 to 1.0
            self.consecutive_attacks / 5.0,  # Scaled 0.0 to 1.0
            float(self.is_in_range),  # Pass the simple 0 or 1 range state
            float(self.human_is_left)
        ], dtype=np.float32)
        done = self.current_step >= 200  # End episode safely to naturally reset
        return state, reward, done, False, {}

if __name__ == "__main__":
    # 2. Train the AI
    env = BossAIEnv()
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=50000)

    # 3. Save the "Brain" to use in your game
    model.save("boss_reaction_model")