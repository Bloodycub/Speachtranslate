import logging
logging.basicConfig(level=logging.DEBUG)

from vosk import Model

MODEL_PATH = r"B:\git_addons\vosk-model-ru-0.10"

try:
    model = Model(MODEL_PATH)
    print("Model loaded successfully")
except Exception as e:
    print(f"Failed to load model: {e}")
