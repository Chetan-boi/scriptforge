import io
import sqlite3
from pathlib import Path
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .config import load_config

# Load TOML settings
CFG = load_config()
CHAR_SIZE = float(CFG["page"]["char_size"])
LINE_SPACING = float(CFG["page"]["line_spacing"])
LEFT_MARGIN = float(CFG["page"]["left_margin"])
TOP_MARGIN = float(CFG["page"]["top_margin"])
BOTTOM_MARGIN = float(CFG["page"]["bottom_margin"])

RULE_COLOR = HexColor(CFG["colors"]["rule_line"])
MARGIN_COLOR = HexColor(CFG["colors"]["margin_line"])
DEFAULT_DB = CFG["database"]["default_path"]


def draw_notebook_ruling(c: canvas.Canvas, page_width, page_height) -> None:
    c.saveState()

    c.setStrokeColor(RULE_COLOR)
    c.setLineWidth(0.6)
    y = page_height - TOP_MARGIN
    while y >= BOTTOM_MARGIN:
        c.line(0, y, page_width, y)
        y -= LINE_SPACING

    c.setStrokeColor(MARGIN_COLOR)
    c.setLineWidth(1.0)
    c.line(LEFT_MARGIN, 0, LEFT_MARGIN, page_height)

    c.restoreState()


def load_glyph(db_path) -> dict[str, Image.Image]:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    glyphs = {}
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT char, image FROM glyphs")
        for char, img_blob in cursor.fetchall():
            glyphs[char] = Image.open(io.BytesIO(img_blob))

    return glyphs


def generate_pdf(text, output_path: str | None = None, name: str | None = None) -> Path:
    path_obj = Path(text)
    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
            raise FileNotFoundError(f"{e} : {text}")

    db_file = Path(f"{name}.db") if name else Path(DEFAULT_DB)
    glyph_bank = load_glyph(db_file)

    if not output_path:
        out_file = Path("output.pdf")
    else:
        out_file = Path(output_path)
        if out_file.is_dir():
            out_file = out_file / "output.pdf"
        elif not out_file.name.endswith(".pdf"):
            out_file = Path(f"{out_file}.pdf")

    out_file.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = A4
    c = canvas.Canvas(str(out_file), pagesize=A4)

    draw_notebook_ruling(c, page_width, page_height)

    text_start_x = LEFT_MARGIN + 8.0
    cursor_x = text_start_x
    cursor_y = page_height - TOP_MARGIN

    for char in content:
        if char == "\r":
            continue

        if char == "\n":
            cursor_x = text_start_x
            cursor_y -= LINE_SPACING
            if cursor_y < BOTTOM_MARGIN:
                c.showPage()
                draw_notebook_ruling(c, page_width, page_height)
                cursor_x = text_start_x
                cursor_y = page_height - TOP_MARGIN
            continue

        if cursor_x + CHAR_SIZE > page_width - 20:
            cursor_x = text_start_x
            cursor_y -= LINE_SPACING
            if cursor_y < BOTTOM_MARGIN:
                c.showPage()
                draw_notebook_ruling(c, page_width, page_height)
                cursor_x = text_start_x
                cursor_y = page_height - TOP_MARGIN

        if char == " ":
            cursor_x += CHAR_SIZE * 0.75
            continue

        glyph = glyph_bank.get(char.lower())
        if glyph:
            c.drawImage(
                ImageReader(glyph),
                cursor_x,
                cursor_y,
                width=CHAR_SIZE,
                height=CHAR_SIZE,
                mask="auto",
            )
        else:
            c.setFont("Helvetica", CHAR_SIZE)
            c.drawString(cursor_x, cursor_y, char)

        cursor_x += CHAR_SIZE

    c.save()
    return out_file
