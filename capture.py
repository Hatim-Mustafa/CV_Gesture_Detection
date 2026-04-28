import cv2
import mediapipe as mp
from config import (CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT,
                    MIN_DETECTION_CONFIDENCE, MIN_TRACKING_CONFIDENCE,
                    USE_POSE, PLAYER_ZONE)

class FrameCapture:
    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        if USE_POSE:
            self.detector = mp.solutions.pose.Pose(
                min_detection_confidence=MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=MIN_TRACKING_CONFIDENCE
            )
        else:
            self.detector = mp.solutions.hands.Hands(
                max_num_hands=1,
                min_detection_confidence=MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=MIN_TRACKING_CONFIDENCE
            )

        self.mp_draw = mp.solutions.drawing_utils
        self.use_pose = USE_POSE

    def _crop_zone(self, frame):
        """Crop frame for split-screen PvP."""
        mid = frame.shape[1] // 2
        if PLAYER_ZONE == 'left':
            return frame[:, :mid]
        elif PLAYER_ZONE == 'right':
            return frame[:, mid:]
        return frame  # 'full'

    def get_landmarks(self):
        """
        Returns (landmarks, annotated_frame) or (None, frame) if nothing detected.
        landmarks is a flat list of (x, y, z) tuples normalised to [0,1].
        """
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        frame = self._crop_zone(frame)
        frame = cv2.flip(frame, 1)          # mirror so left/right feel natural
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.detector.process(rgb)
        rgb.flags.writeable = True

        landmarks = None
        if self.use_pose:
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                landmarks = [(p.x, p.y, p.z) for p in lm]
                self.mp_draw.draw_landmarks(
                    frame, results.pose_landmarks,
                    mp.solutions.pose.POSE_CONNECTIONS
                )
        else:
            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0]
                landmarks = [(p.x, p.y, p.z) for p in lm.landmark]
                self.mp_draw.draw_landmarks(
                    frame, lm,
                    mp.solutions.hands.HAND_CONNECTIONS
                )

        return landmarks, frame

    def release(self):
        self.cap.release()