# ── Tunable constants ──────────────────────────────────────────
CAMERA_INDEX     = 0
FRAME_WIDTH      = 640
FRAME_HEIGHT     = 480
TARGET_FPS       = 30

# MediaPipe Tasks API — download these model files once:
#   Hand: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
#   Pose: https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
HAND_MODEL_PATH  = 'models/hand_landmarker.task'
POSE_MODEL_PATH  = 'models/pose_landmarker_lite.task'

USE_POSE         = False       # True = full body, False = hands only

# Confidence thresholds (Tasks API names differ from legacy)
MIN_HAND_DETECTION_CONFIDENCE  = 0.7
MIN_HAND_PRESENCE_CONFIDENCE   = 0.6
MIN_HAND_TRACKING_CONFIDENCE   = 0.6

MIN_POSE_DETECTION_CONFIDENCE  = 0.7
MIN_POSE_PRESENCE_CONFIDENCE   = 0.6
MIN_POSE_TRACKING_CONFIDENCE   = 0.6

# Classifier
DEBOUNCE_FRAMES  = 3
COOLDOWN_SECONDS = 0.25

# PvP split-frame: 'full' | 'left' | 'right'
PLAYER_ZONE      = 'full'
PLAYER_ID        = 1
BOSS_ID          = 0

# Socket
UDP_HOST         = '127.0.0.1'
UDP_PORT         = 5005