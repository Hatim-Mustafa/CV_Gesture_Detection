# download_models.py — run once before first use
import urllib.request, os

os.makedirs('models', exist_ok=True)

models = {
    'models/hand_landmarker.task':
        'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',
    'models/pose_landmarker_lite.task':
        'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task',
}

for path, url in models.items():
    if os.path.exists(path):
        print(f'[skip] {path} already exists')
        continue
    print(f'[download] {path} ...')
    urllib.request.urlretrieve(url, path)
    print(f'[ok] saved {path}')