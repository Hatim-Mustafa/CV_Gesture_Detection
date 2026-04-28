# ── Tunable constants ──────────────────────────────────────────
CAMERA_INDEX     = 0          # change to 1 for external webcam
FRAME_WIDTH      = 640
FRAME_HEIGHT     = 480
TARGET_FPS       = 30

# MediaPipe
USE_POSE         = False       # True = full body, False = hands only
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE  = 0.6

# Classifier
DEBOUNCE_FRAMES  = 3          # gesture must hold this many frames
COOLDOWN_SECONDS = 0.25       # seconds between repeated sends

# For PvP split-frame: 'full' | 'left' | 'right'
PLAYER_ZONE      = 'full'
PLAYER_ID        = 1          # 1 or 2

# Socket
UDP_HOST         = '127.0.0.1'
UDP_PORT         = 5005