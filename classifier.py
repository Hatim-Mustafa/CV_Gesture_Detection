import time
import math
from collections import deque
from config import DEBOUNCE_FRAMES, COOLDOWN_SECONDS, USE_POSE

# ── Gesture IDs ────────────────────────────────────────────────
GESTURES = {
    'NONE':    0,
    'FORWARD': 1,
    'BACK':    2,
    'JUMP':    3,
    'ATTACK':  4,
    'SHIELD':  5,
}

# ── Low-level helpers ──────────────────────────────────────────

def _dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def _finger_extended(lm, tip, pip):
    """Tip y-coord < PIP y-coord means finger pointing up (y increases downward)."""
    return lm[tip][1] < lm[pip][1]

def _fingers_up(lm):
    """Returns [thumb, index, middle, ring, pinky] as booleans."""
    tips = [4,  8, 12, 16, 20]
    pips = [3,  6, 10, 14, 18]   # thumb uses IP instead of PIP
    return [_finger_extended(lm, t, p) for t, p in zip(tips, pips)]

# ── Hand gesture rules ─────────────────────────────────────────
#
#  FORWARD  – point index finger right  (index up, others down, wrist.x < index_tip.x)
#  BACK     – point index finger left   (index up, others down, wrist.x > index_tip.x)
#  JUMP     – open palm facing camera   (all 5 fingers extended)
#  ATTACK   – closed fist               (all 5 fingers curled)
#  SHIELD   – only index + middle up    (victory / peace sign)
#
# Feel free to change these mappings to whatever feels natural in play.

def _classify_hand(lm):
    up = _fingers_up(lm)
    wrist     = lm[0]
    index_tip = lm[8]

    all_up     = all(up)
    all_down   = not any(up)
    only_index = up[1] and not up[2] and not up[3] and not up[4]
    peace      = up[1] and up[2] and not up[3] and not up[4]

    if all_up:
        return 'JUMP'

    if all_down:
        return 'ATTACK'

    if peace:
        return 'SHIELD'

    if only_index:
        # horizontal pointing direction
        if index_tip[0] > wrist[0] + 0.05:   # pointing right → move forward
            return 'FORWARD'
        if index_tip[0] < wrist[0] - 0.05:   # pointing left  → move back
            return 'BACK'

    return 'NONE'

# ── Pose gesture rules (full-body) ────────────────────────────
#
#  Uses a subset of the 33 pose landmarks.
#  Key indices: 0=nose, 11=left_shoulder, 12=right_shoulder,
#               15=left_wrist, 16=right_wrist,
#               27=left_ankle, 28=right_ankle
#
#  FORWARD  – right wrist raised above right shoulder
#  BACK     – left  wrist raised above left  shoulder
#  JUMP     – both  wrists raised above both shoulders
#  ATTACK   – right wrist extended far right (x > shoulder + 0.15)
#  SHIELD   – both  arms crossed at chest level

def _classify_pose(lm):
    r_shoulder = lm[12]
    l_shoulder = lm[11]
    r_wrist    = lm[16]
    l_wrist    = lm[15]

    r_wrist_high  = r_wrist[1] < r_shoulder[1] - 0.05
    l_wrist_high  = l_wrist[1] < l_shoulder[1] - 0.05
    r_wrist_right = r_wrist[0] > r_shoulder[0] + 0.15
    arms_crossed  = (l_wrist[0] > r_shoulder[0] and
                     r_wrist[0] < l_shoulder[0])

    if r_wrist_high and l_wrist_high:
        return 'JUMP'
    if arms_crossed:
        return 'SHIELD'
    if r_wrist_right:
        return 'ATTACK'
    if r_wrist_high:
        return 'FORWARD'
    if l_wrist_high:
        return 'BACK'
    return 'NONE'


# ── Debounce + Cooldown wrapper ────────────────────────────────

class GestureClassifier:
    def __init__(self):
        self._buffer      = deque(maxlen=DEBOUNCE_FRAMES)
        self._last_send   = 0.0
        self._confirmed   = 'NONE'

    def update(self, landmarks):
        """
        Feed in new landmarks. Returns confirmed gesture string
        only when it should be sent (debounced + cooled down).
        Returns None if nothing to send.
        """
        if landmarks is None:
            self._buffer.clear()
            return None

        raw = _classify_pose(landmarks) if USE_POSE else _classify_hand(landmarks)
        self._buffer.append(raw)

        # require all frames in buffer to agree
        if len(self._buffer) < DEBOUNCE_FRAMES:
            return None
        if not all(g == self._buffer[0] for g in self._buffer):
            return None

        stable = self._buffer[0]
        if stable == 'NONE':
            return None

        # cooldown: don't spam the same gesture
        now = time.monotonic()
        if stable == self._confirmed and (now - self._last_send) < COOLDOWN_SECONDS:
            return None

        self._confirmed = stable
        self._last_send = now
        return stable