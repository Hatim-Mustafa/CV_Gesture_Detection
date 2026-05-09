import cv2
import numpy as np
from stable_baselines3 import PPO
from capture    import FrameCapture
from classifier import GestureClassifier

# Define mappings (Must match your ai_agent.py environment)
GESTURE_MAP = {
    'NONE': 0,
    'FORWARD': 1,
    'BACK': 2,
    'JUMP': 3,
    'ATTACK': 4,
    'SHIELD': 5,
}
ACTION_MAP = {0: "IDLE", 1: "ATTACK", 2: "SHIELD", 3: "JUMP", 4: "BACKWARD"}

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

    print("[gesture] running — press Q to quit")

    while True:
        landmarks, frame = cap.get_landmarks()
        if frame is None: break

        # 2. Get the gesture text from your classifier
        gesture_text = classifier.update(landmarks)

        # 3. AI Logic Loop
        boss_move = "WAITING"
        if gesture_text in GESTURE_MAP:
            gesture_id = GESTURE_MAP[gesture_text]

            # 4. Package the observation (Must match your training input)
            # [Human_Gesture, Dist_X, Dist_Y, Boss_Health]
            obs = np.array([gesture_id / 5.0, 0, 0, 1.0], dtype=np.float32)
            
            # 5. Predict the move
            action_id, _ = model.predict(obs, deterministic=False)
            action_id = int(action_id)  # Convert the array to a single integer
            boss_move = ACTION_MAP.get(action_id, "IDLE")
            
            print(f"[Live] Human: {gesture_text} | AI Boss: {boss_move}")

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

if __name__ == '__main__':
    run()