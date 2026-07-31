import os
import numpy as np
from PIL import Image

from django.conf import settings
import tensorflow as tf


class FlowerPredictor:
    def __init__(self):
        self.model_path = getattr(settings, "MODEL_PATH", None)
        if not self.model_path:
            raise RuntimeError("MODEL_PATH n'est pas défini dans settings.py")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Modèle introuvable: {self.model_path}")

        print(f"📁 Chargement modèle: {self.model_path}")

        # si le modèle référence preprocess_input en interne
        self.custom_objects = {
            "preprocess_input": tf.keras.applications.resnet50.preprocess_input
        }

        self.model = self._load_model_robust()

        # classes
        self.class_names = ["daisy", "dandelion", "rose", "sunflower", "tulip"]
        self.translations = {
            "daisy": "marguerite",
            "dandelion": "pissenlit",
            "rose": "rose",
            "sunflower": "tournesol",
            "tulip": "tulipe",
        }
        self.descriptions = {
            "marguerite": "Une belle fleur blanche avec un cœur jaune doré.",
            "pissenlit": "Fleur jaune sauvage aux propriétés médicinales remarquables.",
            "rose": "La reine des fleurs, symbole universel d'amour et de passion.",
            "tournesol": "Grande fleur jaune éclatante qui suit le soleil.",
            "tulipe": "Fleur élégante et colorée, symbole du printemps.",
        }

        # taille d'entrée
        input_shape = self.model.input_shape
        if isinstance(input_shape, list):
            input_shape = input_shape[0]
        self.target_size = (int(input_shape[1]), int(input_shape[2]))

        # nombre d'inputs
        try:
            self.n_inputs = len(self.model.inputs)
        except Exception:
            self.n_inputs = 1

        print(f"✅ Modèle prêt | target_size={self.target_size} | n_inputs={self.n_inputs}")

        # IMPORTANT :
        # - laisse False si ton modèle applique preprocess_input en interne
        # - mets True si ton modèle attend preprocess_input côté Python
        self.apply_resnet_preprocess_here = False

    def _load_model_robust(self):
        # 1) tf.keras avec safe_mode=False (keras récent)
        try:
            m = tf.keras.models.load_model(
                self.model_path,
                custom_objects=self.custom_objects,
                compile=False,
                safe_mode=False,
            )
            print("✅ load_model: tf.keras (safe_mode=False)")
            return m
        except TypeError:
            pass
        except Exception as e:
            last_err = e
        else:
            last_err = None

        # 2) tf.keras sans safe_mode
        try:
            m = tf.keras.models.load_model(
                self.model_path,
                custom_objects=self.custom_objects,
                compile=False,
            )
            print("✅ load_model: tf.keras (sans safe_mode)")
            return m
        except Exception as e:
            last_err = e

        # 3) keras legacy loader (corrige souvent pop(..., ...) sur vieux H5)
        try:
            from keras.src.legacy.saving import legacy_h5_format

            m = legacy_h5_format.load_model_from_hdf5(
                self.model_path,
                custom_objects=self.custom_objects,
                compile=False,
            )
            print("✅ load_model: keras legacy_h5_format")
            return m
        except Exception as e3:
            raise RuntimeError(
                "Impossible de charger le modèle .h5 (incompatibilité Keras/TF).\n"
                f"- Erreur tf.keras: {last_err}\n"
                f"- Erreur legacy_h5_format: {e3}"
            )

    def preprocess_image(self, image_path: str):
        img = Image.open(image_path).convert("RGB")
        img = img.resize(self.target_size, Image.Resampling.LANCZOS)

        x = np.array(img, dtype=np.float32)
        x = np.expand_dims(x, axis=0)  # (1,H,W,3)

        if self.apply_resnet_preprocess_here:
            x = tf.keras.applications.resnet50.preprocess_input(x)

        return x

    def predict(self, image_path: str):
        x = self.preprocess_image(image_path)

        if self.n_inputs == 2:
            preds = self.model.predict([x, x], verbose=0)
        else:
            preds = self.model.predict(x, verbose=0)

        if isinstance(preds, (list, tuple)):
            preds = preds[0]

        preds = np.array(preds[0], dtype=np.float32)

        # si ce ne sont pas des probas, on softmax
        s = float(preds.sum())
        if not (np.all(preds >= 0) and np.all(preds <= 1) and abs(s - 1.0) < 1e-2):
            preds = tf.nn.softmax(preds).numpy()

        idx = int(np.argmax(preds))
        en = self.class_names[idx]
        fr = self.translations.get(en, en)
        confidence = float(preds[idx] * 100.0)

        all_probs = []
        for i, cname in enumerate(self.class_names):
            all_probs.append({
                "class": self.translations.get(cname, cname),
                "probability": float(preds[i] * 100.0),
            })
        all_probs.sort(key=lambda d: d["probability"], reverse=True)

        return {
            "predicted_class": fr,
            "confidence": round(confidence, 2),
            "description": self.descriptions.get(fr, ""),
            "all_probabilities": all_probs,
        }


_predictor_instance = None


def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        print("🔄 Initialisation prédicteur...")
        _predictor_instance = FlowerPredictor()
    return _predictor_instance
