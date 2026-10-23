# import io 
import os
import random
import sqlite3
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def load_glyph(db_path) -> dict[str,Image.Image]:
    path = Path(db_path)

    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    glyphs = {}
    with sqlite3.connect(path) as conn:
        cursor = con.cursor()
        cursor.execute("SELECT char, image FROM glyphs")
        for char, img_blob in cursor.fetchall():
            glyphs[char] = Image.open(io.BytesIO(img_blob))

    return glyphs

def generate_pdf(text,output_path,name):
    content = ""
    if os.path.exists(text):
        try:
            with open(text,"r") as f:
                content = f.read()
        except Exception:
            content = text

    pass
    db_file = Path(f"{name}.db") if name else Path(".bim/default.db")
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

    cursor_x = 0.0
    cursor_y = page_height - char_size

    for char in content:
        # Handle explicit newlines
        if char == "\n":
            cursor_x = 0.0
            cursor_y -= line_spacing
            if cursor_y < 0:
                c.showPage()
                cursor_x = 0.0
                cursor_y = page_height - char_size
            continue

        # Wrap at the right edge without margin padding
        if cursor_x + char_size > page_width:
            cursor_x = 0.0
            cursor_y -= line_spacing
            if cursor_y < 0:
                c.showPage()
                cursor_x = 0.0
                cursor_y = page_height - char_size

        if char == " ":
            cursor_x += char_size
            continue

        glyph = glyph_bank.get(char.lower())
        if glyph:
            c.drawImage(
                ImageReader(glyph),
                cursor_x,
                cursor_y,
                width=char_size,
                height=char_size,
            )
            cursor_x += char_size
        else:
            c.setFont("Helvetica", char_size)
            c.drawString(cursor_x, cursor_y, char)
            cursor_x += char_size

    c.save()
    return out_file

