# utils/predict.py
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from tensorflow.keras.applications.imagenet_utils import preprocess_input

# Correct path to model
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # go one level up
model_path = os.path.join(basedir, 'model', 'blood_group_detection.h5')

model = load_model(model_path)

labels = {
    0: 'A+', 1: 'A-', 2: 'AB+', 3: 'AB-',4: 'B+', 5: 'B-', 6: 'O+', 7: 'O-'
}

def predict_blood_group(img_path):
    img = image.load_img(img_path, target_size=(256, 256), color_mode='rgb')
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    result = model.predict(x)
    predicted_class = np.argmax(result)
    predicted_label = labels.get(predicted_class, "Unknown")
    confidence = result[0][predicted_class] * 100

    return predicted_label, confidence
