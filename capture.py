import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT,
    HAND_MODEL_PATH, POSE_MODEL_PATH, USE_POSE,
    MIN_HAND_DETECTION_CONFIDENCE, MIN_HAND_PRESENCE_CONFIDENCE,
    MIN_HAND_TRACKING_CONFIDENCE,
    MIN_POSE_DETECTION_CONFIDENCE, MIN_POSE_PRESENCE_CONFIDENCE,
    MIN_POSE_TRACKING_CONFIDENCE,
    PLAYER_ZONE,
)

# ── Landmark drawing constants ─────────────────────────────────
# Hand connections (21 landmarks): pairs of indices to draw skeleton
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),         # thumb
    (0,5),(5,6),(6,7),(7,8),         # index
    (0,9),(9,10),(10,11),(11,12),    # middle
    (0,13),(13,14),(14,15),(15,16),  # ring
    (0,17),(17,18),(18,19),(19,20),  # pinky
    (5,9),(9,13),(13,17),            # palm
]

# Pose connections (33 landmarks): key pairs for a basic skeleton
POSE_CONNECTIONS = [
    (11,12),(11,13),(13,15),(12,14),(14,16),  # arms
    (11,23),(12,24),(23,24),                  # torso
    (23,25),(25,27),(24,26),(26,28),          # legs
]


class FrameCapture:
    """
    Wraps webcam capture + MediaPipe Tasks API detection.

    Uses VisionRunningMode.VIDEO which is correct for a while-loop
    reading frames from a webcam — it enables inter-frame tracking
    (reducing latency vs IMAGE mode) without needing async callbacks.
    Each call to get_landmarks() passes a monotonic timestamp so the
    tracker can interpolate between detections.
    """

    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self._start_time_ms = int(time.monotonic() * 1000)

        if USE_POSE:
            self._detector = self._build_pose_landmarker()
        else:
            self._detector = self._build_hand_landmarker()

        self.use_pose = USE_POSE

    # ── Builder helpers ────────────────────────────────────────

    def _build_hand_landmarker(self):
        options = mp_vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(
                model_asset_path=HAND_MODEL_PATH
            ),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=MIN_HAND_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=MIN_HAND_PRESENCE_CONFIDENCE,
            min_tracking_confidence=MIN_HAND_TRACKING_CONFIDENCE,
        )
        return mp_vision.HandLandmarker.create_from_options(options)

    def _build_pose_landmarker(self):
        options = mp_vision.PoseLandmarkerOptions(
            base_options=mp_python.BaseOptions(
                model_asset_path=POSE_MODEL_PATH
            ),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=MIN_POSE_DETECTION_CONFIDENCE,
            min_pose_presence_confidence=MIN_POSE_PRESENCE_CONFIDENCE,
            min_tracking_confidence=MIN_POSE_TRACKING_CONFIDENCE,
            output_segmentation_masks=False,
        )
        return mp_vision.PoseLandmarker.create_from_options(options)

    # ── Internal helpers ───────────────────────────────────────

    def _crop_zone(self, frame):
        """Crop frame half for split-screen PvP."""
        mid = frame.shape[1] // 2
        if PLAYER_ZONE == 'left':
            return frame[:, :mid]
        elif PLAYER_ZONE == 'right':
            return frame[:, mid:]
        return frame

    def _timestamp_ms(self):
        """Monotonic timestamp in ms — required by VIDEO mode."""
        return int(time.monotonic() * 1000) - self._start_time_ms

    def _draw_landmarks(self, frame, landmarks_list, connections):
        """
        Draw landmark dots and skeleton lines directly with OpenCV.
        landmarks_list: list of NormalizedLandmark objects (x, y normalised to [0,1])
        """
        h, w = frame.shape[:2]
        # Convert normalised coords to pixel coords
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks_list]
        for (i, j) in connections:
            if i < len(pts) and j < len(pts):
                cv2.line(frame, pts[i], pts[j], (0, 200, 100), 1)
        for (px, py) in pts:
            cv2.circle(frame, (px, py), 3, (255, 255, 255), -1)

    # ── Public API ─────────────────────────────────────────────

    def get_landmarks(self):
        """
        Read one frame, run detection, return (landmarks, annotated_frame).

        landmarks: list of (x, y, z) tuples normalised to [0,1], or None
        annotated_frame: BGR numpy array with skeleton drawn, or None on camera failure
        """
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        frame = self._crop_zone(frame)
        frame = cv2.flip(frame, 1)  # mirror so movement feels natural

        # New Tasks API requires RGB numpy array wrapped in mp.Image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        ts        = self._timestamp_ms()

        landmarks = None

        if self.use_pose:
            result = self._detector.detect_for_video(mp_image, ts)
            # result.pose_landmarks is a list of poses; each pose is a list of
            # NormalizedLandmark with .x .y .z .visibility .presence
            if result.pose_landmarks:
                lm_list   = result.pose_landmarks[0]   # first detected pose
                landmarks = [(lm.x, lm.y, lm.z) for lm in lm_list]
                self._draw_landmarks(frame, lm_list, POSE_CONNECTIONS)
        else:
            result = self._detector.detect_for_video(mp_image, ts)
            # result.hand_landmarks is a list of hands; each hand is a list of
            # NormalizedLandmark with .x .y .z
            if result.hand_landmarks:
                lm_list   = result.hand_landmarks[0]   # first detected hand
                landmarks = [(lm.x, lm.y, lm.z) for lm in lm_list]
                self._draw_landmarks(frame, lm_list, HAND_CONNECTIONS)

        return landmarks, frame

    def release(self):
        self._detector.close()
        self.cap.release()