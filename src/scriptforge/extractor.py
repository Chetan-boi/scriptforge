from pathlib import Path
import sqlite3
import string
import cv2

LABELS = list(string.ascii_lowercase) + [str(i) for i in range(10)]


def extract_glyphs(img_path: str, name: str | None = None) -> Path:
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"Could not open image: {img_path}")

    if name:
        db_path = Path(f"{name}.db")
    else:
        db_path = Path(".bin/default.db")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS glyphs (char TEXT PRIMARY KEY, image BLOB NOT NULL)"
        )

        height, width, _ = img.shape
        cell_h = height // 6
        cell_w = width // 6

        records = []
        i = 0

        # not working
        for r in range(6):
            for c in range(6):
                char = LABELS[i]
                crop = img[
                    r * cell_h : (r + 1) * cell_h, c * cell_w : (c + 1) * cell_w
                ]

                success, buffer = cv2.imencode(".png", crop)
                if success:
                    records.append((char, buffer.tobytes()))
                i += 1

        conn.executemany(
            "INSERT OR REPLACE INTO glyphs (char, image) VALUES (?, ?)",
            records,
        )

    return db_path
