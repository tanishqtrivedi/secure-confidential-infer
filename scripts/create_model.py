import tensorflow as tf
from pathlib import Path

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(224, 224, 3)),
    tf.keras.layers.Conv2D(16, 3, activation="relu"),
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(1, activation="sigmoid"),
])

model.compile(optimizer="adam", loss="binary_crossentropy")

out_dir = Path("model")
out_dir.mkdir(exist_ok=True)
model_path = out_dir / "medical_model.keras"
model.save(model_path)
print("Model saved to", model_path)
