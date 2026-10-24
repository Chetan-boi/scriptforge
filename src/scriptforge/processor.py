import cv2
import numpy as np

def remove_background(crop_bgr: np.ndarray) -> bytes:
    # convert to greyscale
    gray = cv2.cvtColor(crop_bgr,cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    h, w = gray.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Set ink color values (e.g., dark ink #1e1e1e)
    rgba[:, :, 0] = 30  # Blue
    rgba[:, :, 1] = 30  # Green
    rgba[:, :, 2] = 30  # Red
    rgba[:, :, 3] = binary  # Alpha channel: transparent where paper was, solid on ink

    # Encode directly to PNG bytes for SQLite storage
    success, buffer = cv2.imencode(".png", rgba)
    if not success:
        raise ValueError("Failed to encode transparent glyph image")

    return buffer.tobytes()
