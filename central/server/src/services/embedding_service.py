"""
Face embedding generation service.

Uses OpenCV's SFace model to extract 128D face embeddings from base64-encoded photos.
The SFace ONNX model must be available at the path configured below.

NOTE: On the Central Server, this service is used during person registration.
      The Edge Node uses its own local copy of the models for real-time processing.
"""

import base64

import cv2
import numpy as np


class MultipleFacesError(Exception):
    """Raised when more than one face is detected in a photo."""
    pass


class NoFaceError(Exception):
    """Raised when no face is detected in a photo."""
    pass


# Pre-load models (loaded once on first import)
_detector = None
_recognizer = None

YUNET_MODEL_PATH = "models_cv/yunet.onnx"
SFACE_MODEL_PATH = "models_cv/sface.onnx"


def _get_detector():
    global _detector
    if _detector is None:
        _detector = cv2.FaceDetectorYN.create(YUNET_MODEL_PATH, "", (0, 0))
    return _detector


def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = cv2.FaceRecognizerSF.create(SFACE_MODEL_PATH, "")
    return _recognizer


def extract_embedding_from_base64(photo_b64: str) -> list[float]:
    """
    Decode a base64 image, detect exactly one face, and return a 128D embedding.
    Raises NoFaceError if no face is detected.
    Raises MultipleFacesError if more than one face is detected.
    """
    try:
        img_bytes = base64.b64decode(photo_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            raise NoFaceError("Could not decode image")

        detector = _get_detector()
        h, w = img.shape[:2]
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)

        if faces is None or len(faces) == 0:
            raise NoFaceError("No face detected in the photo")

        if len(faces) > 1:
            raise MultipleFacesError(
                f"Expected 1 face, but found {len(faces)}"
            )

        face = faces[0]
        recognizer = _get_recognizer()
        aligned = recognizer.alignCrop(img, face)
        embedding = recognizer.feature(aligned)

        return embedding.flatten().tolist()

    except (MultipleFacesError, NoFaceError):
        raise
    except Exception:
        raise NoFaceError("Failed to process image")
