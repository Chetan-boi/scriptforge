"""ScriptForge desktop window (CustomTkinter)"""
import os
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .utils import extract_glyphs, generate_pdf

DESK = "#E6EAF0"
PAPER = "#FCFCFD"
INK = "#1D2B4F"
INK_HOVER = "#2E4073"
MUTED = "#5F6B80"
RULE = "#B0C4DE"
MARGIN = "#E57373"


def open_file(path):
    """Open a file in whatever app the OS uses for it."""
    if sys.platform == "darwin": #for macos
        subprocess.run(["open", path])
    elif sys.platform == "win32": #for windows
        os.startfile(path)
    else:
        subprocess.run(["xdg-open", path])


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScriptForge")
        self.geometry("920x600")
        self.minsize(800, 520)

        self.f_title = ctk.CTkFont(size=26, weight="bold")
        self.f_head = ctk.CTkFont(size=16, weight="bold")
        self.f_body = ctk.CTkFont(size=13)
        self.f_write = ctk.CTkFont(size=16)

        self.profile = None  
        self.last_pdf = None
        self.buttons = []     

        self.build_sidebar()
        self.build_page()

    # ---------- layout ----------

    def make_button(self, parent, text, command, primary=False):
        if primary:
            btn = ctk.CTkButton(
                parent, text=text, command=command, font=self.f_body,
                height=36, corner_radius=3,
                fg_color=INK, hover_color=INK_HOVER, text_color="white",
            )
        else:
            btn = ctk.CTkButton(
                parent, text=text, command=command, font=self.f_body,
                height=36, corner_radius=3,
                fg_color="transparent", hover_color="#D5DBE6",
                border_width=1, border_color=INK, text_color=INK,
            )
        self.buttons.append(btn)
        return btn

    def build_sidebar(self):
        side = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=DESK)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)   

        ctk.CTkLabel(side, text="ScriptForge", font=self.f_title, text_color=INK
                     ).pack(anchor="w", padx=24, pady=(28, 2))
        ctk.CTkLabel(side, text="Turn typed text into your own handwriting.",
                     font=self.f_body, text_color=MUTED, wraplength=250, justify="left"
                     ).pack(anchor="w", padx=24)

        ctk.CTkLabel(side, text="Your handwriting", font=self.f_head, text_color=INK
                     ).pack(anchor="w", padx=24, pady=(40, 4))
        ctk.CTkLabel(side, text="Upload a photo of the sheet where you wrote a to z, one letter per box.",
                     font=self.f_body, text_color=MUTED, wraplength=250, justify="left"
                     ).pack(anchor="w", padx=24, pady=(0, 14))

        self.make_button(side, "Choose sheet photo", self.pick_sheet, primary=True
                         ).pack(fill="x", padx=24)
        self.make_button(side, "Use saved profile", self.pick_profile
                         ).pack(fill="x", padx=24, pady=(8, 0))

        self.hw_label = ctk.CTkLabel(side, text="Using the default saved handwriting.",
                                     font=self.f_body, text_color=MUTED,
                                     wraplength=250, justify="left")
        self.hw_label.pack(anchor="w", padx=24, pady=(14, 0))


        self.status = ctk.CTkLabel(side, text="Ready.", font=self.f_body, text_color=INK,
                                   wraplength=250, justify="left")
        self.status.pack(side="bottom", anchor="w", padx=24, pady=(0, 24))
        self.progress = ctk.CTkProgressBar(side, mode="indeterminate", height=5,
                                           corner_radius=2, fg_color=RULE, progress_color=INK)

    def build_page(self):
        page = ctk.CTkFrame(self, corner_radius=0, fg_color=PAPER)
        page.pack(side="left", fill="both", expand=True)

        ctk.CTkFrame(page, width=2, corner_radius=0, fg_color=MARGIN
                     ).pack(side="left", fill="y", padx=(44, 0))

        content = ctk.CTkFrame(page, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(20, 28), pady=24)

        ctk.CTkLabel(content, text="What to write", font=self.f_head, text_color=INK
                     ).pack(anchor="w")
        ctk.CTkFrame(content, height=1, corner_radius=0, fg_color=RULE
                     ).pack(fill="x", pady=(8, 10))

        self.box = ctk.CTkTextbox(content, font=self.f_write, fg_color=PAPER,
                                  text_color=INK, border_width=0, wrap="word")
        self.box.pack(fill="both", expand=True)
        self.box.focus()

        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x", pady=(14, 0))
        self.make_button(row, "Make PDF", self.make_pdf, primary=True).pack(side="right")
        self.open_btn = self.make_button(row, "Open PDF", self.open_last)

    # ---------- button actions ----------

    def pick_sheet(self):
        path = filedialog.askopenfilename(
            title="Choose your handwriting sheet",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff"), ("All files", "*.*")],
        )
        if not path: 
            return
        self.run_in_background(
            work=lambda: extract_glyphs(path),
            busy="Reading sheet",
            done=lambda: self.sheet_done(path),
        )

    def pick_profile(self):
        path = filedialog.askopenfilename(
            title="Choose a saved profile",
            filetypes=[("Handwriting profile", "*.db")],
        )
        if not path:
            return
        self.profile = path.removesuffix(".db")   
        self.hw_label.configure(text=f"Using {Path(path).name}")
        self.status.configure(text="Profile loaded.")

    def make_pdf(self):
        text = self.box.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("ScriptForge", "Type some text first.")
            return
        out = filedialog.asksaveasfilename(
            title="Save PDF as", defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")], initialfile="handwritten.pdf",
        )
        if not out:
            return
        profile = self.profile 

        txt = Path(tempfile.gettempdir()) / "scriptforge_input.txt"
        txt.write_text(text, encoding="utf-8")

        self.run_in_background(
            work=lambda: generate_pdf(str(txt), out, profile),
            busy="Making PDF",
            done=lambda: self.pdf_done(out),
        )

    def open_last(self):
        if self.last_pdf:
            open_file(self.last_pdf)

    # ---------- when the engine finishes ----------

    def sheet_done(self, path):
        self.profile = None  
        self.hw_label.configure(text=f"Learned from {Path(path).name}")
        self.status.configure(text="Sheet read. Type something and make a PDF.")

    def pdf_done(self, out):
        if not Path(out).exists():
            messagebox.showerror("ScriptForge", f"The engine finished but {out} was not created.")
            self.status.configure(text="PDF was not created.")
            return
        self.last_pdf = out
        self.status.configure(text=f"PDF saved: {Path(out).name}")
        self.open_btn.pack(side="left")


    def run_in_background(self, work, busy, done):
        self.set_busy(True, busy)
        result = queue.Queue()   

        def job():
            try:
                work()
                result.put(None)   
            except (Exception, SystemExit) as err:   
                result.put(err)

        threading.Thread(target=job, daemon=True).start()
        self.after(100, self.check, result, done)

    def check(self, result, done):
        try:
            outcome = result.get_nowait()
        except queue.Empty:
            self.after(100, self.check, result, done)   
            return

        self.set_busy(False)
        if outcome is None:
            done()
            return
        self.status.configure(text="That didn't work.")
        detail = str(outcome) if isinstance(outcome, Exception) else ""
        messagebox.showerror(
            "ScriptForge",
            detail or "The engine stopped without a message. The terminal may show more.",
        )

    def set_busy(self, busy, text=None):
        for btn in self.buttons:
            btn.configure(state="disabled" if busy else "normal")
        if busy:
            self.progress.pack(side="bottom", fill="x", padx=24, pady=(0, 8))
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.pack_forget()
        if text:
            self.status.configure(text=text)


def main():
    ctk.set_appearance_mode("light")
    App().mainloop()


if __name__ == "__main__":
    main()
