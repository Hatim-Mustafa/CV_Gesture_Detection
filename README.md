# CV Gesture Detection

A real-time gesture recognition system that captures hand and body poses using your webcam, classifies gestures, and sends them over UDP to control a fighting game. Uses **MediaPipe Tasks API** for efficient on-device machine learning.

## Features

- 🎥 **Real-time gesture detection** using MediaPipe hand and pose landmarking
- 👋 **Hand gesture recognition** (pointing, open palm, fist, peace sign)
- 🧍 **Full-body pose detection** (optional) for enhanced gesture recognition
- 📡 **UDP networking** to communicate with game clients
- 🎮 **PvP support** with player-specific zones (full, left, or right split-screen)
- ⚙️ **Highly configurable** confidence thresholds, debouncing, and cooldown timers
- 🚀 **Lightweight & efficient** using TensorFlow Lite models

## Supported Gestures

### Hand-Based Gestures
| Gesture | Trigger | In-Game Action |
|---------|---------|----------------|
| **FORWARD** | Point index finger right | Move forward |
| **BACK** | Point index finger left | Move backward |
| **JUMP** | Open palm (all fingers extended) | Jump |
| **ATTACK** | Closed fist (spider pose) | Attack/Punch |
| **SHIELD** | Peace sign (index + middle fingers up) | Defend/Shield |

### Pose-Based Gestures (optional)
| Gesture | Trigger | In-Game Action |
|---------|---------|----------------|
| **FORWARD** | Right wrist above right shoulder | Move forward |
| **BACK** | Left wrist above left shoulder | Move backward |
| **JUMP** | Both wrists above both shoulders | Jump |
| **ATTACK** | Right wrist extended far right | Attack |
| **SHIELD** | Both arms crossed at chest | Defend |

## Requirements

- Python 3.8+
- OpenCV (`cv2`)
- MediaPipe
- A webcam

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd CV-Based-Fighting-Game
```

### 2. Install dependencies
```bash
pip install opencv-python mediapipe
```

### 3. Download MediaPipe models
Run the model downloader script once before first use:
```bash
python download_models.py
```

This downloads:
- `hand_landmarker.task` (~30 MB) - Hand pose detection
- `pose_landmarker_lite.task` (~23 MB) - Full-body pose detection

Models are stored in the `models/` directory.

## Usage

### Start the gesture recognition system
```bash
python main.py
```

The system will:
1. Open your webcam feed
2. Display a debug window with detected gestures overlaid
3. Send recognized gestures via UDP to the configured host/port
4. Press **Q** to quit

### Example Output
```
[gesture] running — press Q to quit
[gesture] → JUMP
[gesture] → ATTACK
[gesture] → SHIELD
[gesture] → FORWARD
```

## Configuration

Edit [config.py](config.py) to customize behavior:

### Camera Settings
```python
CAMERA_INDEX     = 0         # Webcam index (0 = default)
FRAME_WIDTH      = 640       # Capture width in pixels
FRAME_HEIGHT     = 480       # Capture height in pixels
TARGET_FPS       = 30        # Target frame rate
```

### Detection Confidence
```python
MIN_HAND_DETECTION_CONFIDENCE  = 0.7   # 0–1, higher = stricter
MIN_HAND_PRESENCE_CONFIDENCE   = 0.6
MIN_HAND_TRACKING_CONFIDENCE   = 0.6
```

### Gesture Processing
```python
DEBOUNCE_FRAMES  = 3         # Frames to confirm gesture stability
COOLDOWN_SECONDS = 0.25      # Minimum time between gesture sends
```

### Network
```python
UDP_HOST         = '127.0.0.1'  # Target IP (localhost for same machine)
UDP_PORT         = 5005         # Target port
PLAYER_ID        = 1            # Player identifier (for PvP)
```

### Game Mode
```python
USE_POSE         = False        # True = full-body, False = hands only
PLAYER_ZONE      = 'full'       # 'full' | 'left' | 'right' (PvP split-screen)
```

## Project Structure

```
CV-Based-Fighting-Game/
├── main.py                    # Entry point; orchestrates capture → classify → send
├── capture.py                 # FrameCapture: webcam + MediaPipe detection
├── classifier.py              # GestureClassifier: gesture recognition rules
├── sender.py                  # GestureSender: UDP networking
├── config.py                  # Configuration constants
├── download_models.py         # Download MediaPipe model files (run once)
├── models/
│   ├── hand_landmarker.task   # Hand detection model (~30 MB)
│   └── pose_landmarker_lite.task  # Pose detection model (~23 MB)
└── README.md                  # This file
```

## How It Works

```
Webcam Feed
    ↓
[capture.py] — MediaPipe landmark detection
    ↓
Landmark coordinates (x, y, z)
    ↓
[classifier.py] — Gesture classification rules
    ↓
Gesture name (JUMP, ATTACK, etc.)
    ↓
[sender.py] — Send via UDP
    ↓
Game receives JSON payload
```

### Detection Pipeline

1. **Frame Capture** (`capture.py`):
   - Reads frames from webcam
   - Runs MediaPipe detection in `VIDEO` mode (supports inter-frame tracking)
   - Returns 21 hand landmarks (or 33 pose landmarks if `USE_POSE=True`)
   - Landmarks are normalized (0–1) pixel coordinates

2. **Gesture Classification** (`classifier.py`):
   - Analyzes landmark positions to determine gesture
   - Applies debouncing (requires consistent gesture for N frames)
   - Enforces cooldown timer to avoid rapid-fire commands

3. **Network Send** (`sender.py`):
   - Encodes gesture as JSON
   - Sends UDP packet to game server

## Network Protocol

Packets are sent as UTF-8 encoded JSON:

```json
{
  "player": 1,
  "gesture": "ATTACK"
}
```

**Host**: `UDP_HOST` (default: `127.0.0.1`)  
**Port**: `UDP_PORT` (default: `5005`)

## Troubleshooting

### Gestures not detected?
- Check lighting — ensure you have good lighting on your hands
- Verify camera is working: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`
- Lower confidence thresholds in `config.py`
- Check camera index with `CAMERA_INDEX = 1` or `2` if default doesn't work

### Models not found?
- Run `python download_models.py` to download MediaPipe models
- Verify `models/` directory exists and contains `.task` files

### UDP packets not reaching game?
- Verify game is listening on `UDP_PORT`
- Check firewall isn't blocking UDP port
- Test locally first with `UDP_HOST = '127.0.0.1'`
- Use a network monitor (e.g., Wireshark) to verify packets are sent

### Poor recognition or jitter?
- Increase `DEBOUNCE_FRAMES` to require more frame consistency
- Increase `COOLDOWN_SECONDS` to space out commands
- Improve lighting or camera angle
- Adjust min confidence thresholds

## Future Enhancements

- [ ] Add support for custom gesture training
- [ ] Multi-hand detection
- [ ] Gesture recording/playback
- [ ] Web-based UI for real-time config adjustments
- [ ] Performance profiling and optimization
- [ ] Support for additional mediapipe solutions (face, object detection)

## License

MIT

## Contributing

Contributions welcome! Feel free to submit issues and pull requests.