import cv2
import numpy as np
import time
import random
from stable_baselines3 import PPO
from capture    import FrameCapture
from classifier import GestureClassifier
from config import BOSS_ID, PLAYER_ID
from sender     import GestureSender
from state_receiver import StateReceiver
from ai_agent   import inRange

# Define mappings (Must match your ai_agent.py environment)
GESTURE_MAP = {
    'NONE': 0,
    'FORWARD': 1,
    'BACK': 2,
    'JUMP': 3,
    'ATTACK': 4,
    'SHIELD': 5,
}
# ACTION_MAP must exactly match your ai_agent.py environment
ACTION_MAP = {0: "IDLE", 1: "ATTACK", 2: "SHIELD", 3: "JUMP", 4: "FORWARD", 5: "BACKWARD"}

def run():
    # 1. Load the Brain
    try:
        model = PPO.load("boss_reaction_model")
        print("[AI] Model loaded successfully.")
    except:
        print("[Error] Could not find boss_reaction_model.zip!")
        return

    cap        = FrameCapture()
    classifier = GestureClassifier()
    sender     = GestureSender()
    state_rx   = StateReceiver()


    print("[gesture] running — press Q to quit")
    last_print_time = time.time()

    while True:
        landmarks, frame = cap.get_landmarks()

        state_rx.update()
        state = state_rx.get()
        # print(state)  # Removed spammy state printing
        
        if frame is None: break
        # 2. Get the gesture text from your classifier
        gesture_text = classifier.update(landmarks)

        # Fallback to NONE so the AI still knows what you are doing
        current_human_gesture = gesture_text if gesture_text else 'NONE'
        gesture_id = GESTURE_MAP[current_human_gesture]

        # 3. AI Logic Loop (Runs continuously, not just when you move)
        boss_move = "WAITING"

        # 4. Package the observation
        # Extract real state info from the C++ game
        px, py = state['player']['x'], state['player']['y']
        bx, by = state['enemy']['x'], state['enemy']['y']
        boss_health = state['enemy']['hp']
        
        # Use the exact same threshold logic as training
        is_in_range, _ = inRange((px, py), (bx, by), threshold=200.0)
        human_is_left = px < bx

        # [Human_Gesture, Boss_Health, Consecutive_Attacks, inRange boolean, is_human_on_left boolean]
        obs = np.array([gesture_id / 5.0, boss_health / 100.0, 0.0, float(is_in_range), float(human_is_left)], dtype=np.float32)
        
        # 5. Predict the move
        action_id, _ = model.predict(obs, deterministic=False)
        action_id = int(action_id)  # Convert the array to a single integer
        boss_move = ACTION_MAP.get(action_id, "IDLE")
        
        # Send the continuous boss state to the C++ game over UDP
        sender.send(gesture=boss_move, player_id=BOSS_ID)

        current_time = time.time()
        # Print status if 0.5 seconds have passed OR if the human did a brand new gesture
        if gesture_text or (current_time - last_print_time >= 0.5):
            print(f"[Live] Human: {current_human_gesture} | AI Boss: {boss_move} | Data: {state}")
            last_print_time = current_time

        # Only send the player gesture if there's an actual, new debounced gesture
        if gesture_text:
            sender.send(gesture=gesture_text,player_id=PLAYER_ID)

        # 6. Debug overlay
        if frame is not None:
            # Show what YOU are doing
            cv2.putText(frame, f"YOU: {gesture_text or '...'}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 120), 2)
            
            # Show what the BOSS decided
            cv2.putText(frame, f"BOSS: {boss_move}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            cv2.imshow("Gesture Debug", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    sender.close()

if __name__ == '__main__':
    run()