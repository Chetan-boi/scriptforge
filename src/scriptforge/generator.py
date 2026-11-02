import io
import sqlite3
from pathlib import Path
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .config import load_config

# Load default TOML settings at module level for compatibility
CFG = load_config()
CHAR_SIZE = float(CFG["page"]["char_size"])
LINE_SPACING = float(CFG["page"]["line_spacing"])
LEFT_MARGIN = float(CFG["page"]["left_margin"])
TOP_MARGIN = float(CFG["page"]["top_margin"])
BOTTOM_MARGIN = float(CFG["page"]["bottom_margin"])

RULE_COLOR = HexColor(CFG["colors"]["rule_line"])
MARGIN_COLOR = HexColor(CFG["colors"]["margin_line"])
DEFAULT_DB = CFG["database"]["default_path"]


def draw_notebook_ruling(c: canvas.Canvas, page_width, page_height, cfg: dict | None = None) -> None:
    if cfg is None:
        cfg = load_config()
    page_cfg = cfg.get("page", {})
    colors_cfg = cfg.get("colors", {})

    top_margin = float(page_cfg.get("top_margin", 50.0))
    bottom_margin = float(page_cfg.get("bottom_margin", 40.0))
    line_spacing = float(page_cfg.get("line_spacing", 24.0))
    left_margin = float(page_cfg.get("left_margin", 54.0))
    show_rules = bool(page_cfg.get("show_rules", True))
    show_margin = bool(page_cfg.get("show_margin", True))
    rule_width = float(page_cfg.get("rule_line_width", 0.6))
    margin_width = float(page_cfg.get("margin_line_width", 1.0))

    rule_color = HexColor(colors_cfg.get("rule_line", "#B0C4DE"))
    margin_color = HexColor(colors_cfg.get("margin_line", "#E57373"))

    c.saveState()

    if show_rules:
        c.setStrokeColor(rule_color)
        c.setLineWidth(rule_width)
        y = page_height - top_margin
        while y >= bottom_margin:
            c.line(0, y, page_width, y)
            y -= line_spacing

    if show_margin:
        c.setStrokeColor(margin_color)
        c.setLineWidth(margin_width)
        c.line(left_margin, 0, left_margin, page_height)

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


def generate_pdf(
    text,
    output_path: str | None = None,
    name: str | None = None,
    cfg: dict | None = None,
) -> Path:
    if cfg is None:
        cfg = load_config()

    page_cfg = cfg.get("page", {})
    char_size = float(page_cfg.get("char_size", 14.0))
    line_spacing = float(page_cfg.get("line_spacing", 24.0))
    left_margin = float(page_cfg.get("left_margin", 54.0))
    right_margin = float(page_cfg.get("right_margin", 20.0))
    top_margin = float(page_cfg.get("top_margin", 50.0))
    bottom_margin = float(page_cfg.get("bottom_margin", 40.0))
    margin_indent = float(page_cfg.get("margin_indent", 8.0))
    space_factor = float(page_cfg.get("space_width_factor", 0.75))
    default_db = cfg.get("database", {}).get("default_path", ".bin/default.db")

    path_obj = Path(text)
    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise FileNotFoundError(f"{e} : {text}")

    if name:
        db_file = Path(name if name.endswith(".db") else f"{name}.db")
    else:
        db_file = Path(default_db)
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

    page_size_name = str(page_cfg.get("size", "A4")).upper()
    pagesize = letter if page_size_name == "LETTER" else A4
    page_width, page_height = pagesize
    c = canvas.Canvas(str(out_file), pagesize=pagesize)

    draw_notebook_ruling(c, page_width, page_height, cfg)

    text_start_x = left_margin + margin_indent
    cursor_x = text_start_x
    cursor_y = page_height - top_margin

    for char in content:
        if char == "\r":
            continue

        if char == "\n":
            cursor_x = text_start_x
            cursor_y -= line_spacing
            if cursor_y < bottom_margin:
                c.showPage()
                draw_notebook_ruling(c, page_width, page_height, cfg)
                cursor_x = text_start_x
                cursor_y = page_height - top_margin
            continue

        if cursor_x + char_size > page_width - right_margin:
            cursor_x = text_start_x
            cursor_y -= line_spacing
            if cursor_y < bottom_margin:
                c.showPage()
                draw_notebook_ruling(c, page_width, page_height, cfg)
                cursor_x = text_start_x
                cursor_y = page_height - top_margin

        if char == " ":
            cursor_x += char_size * space_factor
            continue

        glyph = glyph_bank.get(char.lower())
        if glyph:
            c.drawImage(
                ImageReader(glyph),
                cursor_x,
                cursor_y,
                width=char_size,
                height=char_size,
                mask="auto",
            )
        else:
            c.setFont("Helvetica", char_size)
            c.drawString(cursor_x, cursor_y, char)

        cursor_x += char_size

    c.save()
    return out_file
