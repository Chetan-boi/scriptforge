"""ScriptForge desktop window"""
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .config import DEFAULT_CONFIG, load_config, save_config
from .utils import extract_glyphs, generate_pdf

DESK = "#E6EAF0"
PAPER = "#FCFCFD"
INK = "#1D2B4F"
INK_HOVER = "#2E4073"
MUTED = "#5F6B80"
RULE = "#B0C4DE"
MARGIN = "#E57373"


def open_file(path: str | Path):
    path_str = str(path)
    if sys.platform == "darwin":  # macOS
        subprocess.run(["open", path_str])
    elif sys.platform == "win32":  # Windows
        os.startfile(path_str)
    else:  # Linux
        subprocess.run(["xdg-open", path_str])


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent: "App"):
        super().__init__(parent)
        self.parent = parent
        self.title("ScriptForge Settings")
        self.geometry("540x680")
        self.minsize(480, 520)

        self.transient(parent)
        self.grab_set()

        self.f_head = ctk.CTkFont(size=15, weight="bold")
        self.f_sub = ctk.CTkFont(size=13, weight="bold")
        self.f_body = ctk.CTkFont(size=12)

        self.entries: dict[str, Any] = {}
        self.build_ui()
        self.load_values(parent.cfg)

    def build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(18, 8))
        ctk.CTkLabel(top, text="Settings & Preferences", font=self.f_head, text_color=INK).pack(anchor="w")
        ctk.CTkLabel(
            top,
            text="Tweak page geometry, typography, ruling lines, and theme.",
            font=self.f_body,
            text_color=MUTED,
        ).pack(anchor="w")

        # Scrollable container for settings
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # --- Section: Page Geometry ---
        self.add_section_header(scroll, "Page Geometry & Sizing")
        self.entries["page.size"] = self.add_segmented(
            scroll, "Page Size:", ["A4", "LETTER"]
        )
        self.entries["page.char_size"] = self.add_text_field(
            scroll, "Character Size (pt):", "e.g. 14.0"
        )
        self.entries["page.line_spacing"] = self.add_text_field(
            scroll, "Line Spacing (pt):", "e.g. 24.0"
        )
        self.entries["page.left_margin"] = self.add_text_field(
            scroll, "Left Margin (pt):", "e.g. 54.0"
        )
        self.entries["page.right_margin"] = self.add_text_field(
            scroll, "Right Margin (pt):", "e.g. 20.0"
        )
        self.entries["page.top_margin"] = self.add_text_field(
            scroll, "Top Margin (pt):", "e.g. 50.0"
        )
        self.entries["page.bottom_margin"] = self.add_text_field(
            scroll, "Bottom Margin (pt):", "e.g. 40.0"
        )
        self.entries["page.margin_indent"] = self.add_text_field(
            scroll, "Text Indent after Margin (pt):", "e.g. 8.0"
        )
        self.entries["page.space_width_factor"] = self.add_text_field(
            scroll, "Space Width Factor:", "e.g. 0.75"
        )

        # --- Section: Notebook Ruling ---
        self.add_section_header(scroll, "Notebook Ruling & Lines")
        self.entries["page.show_rules"] = self.add_switch(
            scroll, "Show Horizontal Rule Lines"
        )
        self.entries["page.show_margin"] = self.add_switch(
            scroll, "Show Vertical Margin Line"
        )
        self.entries["page.rule_line_width"] = self.add_text_field(
            scroll, "Rule Line Width (pt):", "e.g. 0.6"
        )
        self.entries["page.margin_line_width"] = self.add_text_field(
            scroll, "Margin Line Width (pt):", "e.g. 1.0"
        )

        # --- Section: Colors ---
        self.add_section_header(scroll, "Colors (Hex Codes)")
        self.entries["colors.rule_line"] = self.add_text_field(
            scroll, "Rule Line Color:", "e.g. #B0C4DE"
        )
        self.entries["colors.margin_line"] = self.add_text_field(
            scroll, "Margin Line Color:", "e.g. #E57373"
        )

        # --- Section: Database ---
        self.add_section_header(scroll, "Database")
        self.entries["database.default_path"] = self.add_text_field(
            scroll, "Default Profile DB Path:", "e.g. .bin/default.db"
        )

        # Bottom Action Bar
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(4, 18))

        ctk.CTkButton(
            bar,
            text="Reset Defaults",
            command=self.reset_defaults,
            font=self.f_body,
            fg_color="transparent",
            border_width=1,
            border_color=MUTED,
            text_color=MUTED,
            hover_color="#D5DBE6",
            width=110,
        ).pack(side="left")

        ctk.CTkButton(
            bar,
            text="Cancel",
            command=self.destroy,
            font=self.f_body,
            fg_color="transparent",
            border_width=1,
            border_color=INK,
            text_color=INK,
            hover_color="#D5DBE6",
            width=80,
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            bar,
            text="Save Settings",
            command=self.save,
            font=self.f_body,
            fg_color=INK,
            hover_color=INK_HOVER,
            text_color="white",
            width=110,
        ).pack(side="right")

    def add_section_header(self, parent, title: str):
        ctk.CTkLabel(
            parent, text=title, font=self.f_sub, text_color=INK
        ).pack(anchor="w", pady=(14, 4))
        ctk.CTkFrame(parent, height=1, fg_color="#D5DBE6").pack(fill="x", pady=(0, 8))

    def add_text_field(self, parent, label: str, placeholder: str = "") -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(row, text=label, font=self.f_body, width=200, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=28, font=self.f_body)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def add_segmented(self, parent, label: str, values: list[str]) -> ctk.CTkSegmentedButton:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(row, text=label, font=self.f_body, width=200, anchor="w").pack(side="left")
        seg = ctk.CTkSegmentedButton(row, values=values, height=28, font=self.f_body)
        seg.pack(side="right", fill="x", expand=True)
        return seg

    def add_switch(self, parent, label: str) -> ctk.CTkSwitch:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        switch = ctk.CTkSwitch(row, text=label, font=self.f_body)
        switch.pack(side="left")
        return switch

    def load_values(self, cfg: dict):
        p = cfg.get("page", {})
        c = cfg.get("colors", {})
        d = cfg.get("database", {})
        u = cfg.get("ui", {})

        self.entries["page.size"].set(str(p.get("size", "A4")).upper())
        self.set_entry("page.char_size", p.get("char_size", 14.0))
        self.set_entry("page.line_spacing", p.get("line_spacing", 24.0))
        self.set_entry("page.left_margin", p.get("left_margin", 54.0))
        self.set_entry("page.right_margin", p.get("right_margin", 20.0))
        self.set_entry("page.top_margin", p.get("top_margin", 50.0))
        self.set_entry("page.bottom_margin", p.get("bottom_margin", 40.0))
        self.set_entry("page.margin_indent", p.get("margin_indent", 8.0))
        self.set_entry("page.space_width_factor", p.get("space_width_factor", 0.75))

        if p.get("show_rules", True):
            self.entries["page.show_rules"].select()
        else:
            self.entries["page.show_rules"].deselect()

        if p.get("show_margin", True):
            self.entries["page.show_margin"].select()
        else:
            self.entries["page.show_margin"].deselect()

        self.set_entry("page.rule_line_width", p.get("rule_line_width", 0.6))
        self.set_entry("page.margin_line_width", p.get("margin_line_width", 1.0))

        self.set_entry("colors.rule_line", c.get("rule_line", "#B0C4DE"))
        self.set_entry("colors.margin_line", c.get("margin_line", "#E57373"))

        self.set_entry("database.default_path", d.get("default_path", ".bin/default.db"))

    def set_entry(self, key: str, value: Any):
        entry = self.entries[key]
        entry.delete(0, "end")
        entry.insert(0, str(value))

    def reset_defaults(self):
        if messagebox.askyesno("Reset Defaults", "Reset all settings to ScriptForge defaults?"):
            self.load_values(DEFAULT_CONFIG)

    def save(self):
        try:
            new_cfg = {
                "page": {
                    "size": self.entries["page.size"].get(),
                    "char_size": float(self.entries["page.char_size"].get().strip()),
                    "line_spacing": float(self.entries["page.line_spacing"].get().strip()),
                    "left_margin": float(self.entries["page.left_margin"].get().strip()),
                    "right_margin": float(self.entries["page.right_margin"].get().strip()),
                    "top_margin": float(self.entries["page.top_margin"].get().strip()),
                    "bottom_margin": float(self.entries["page.bottom_margin"].get().strip()),
                    "margin_indent": float(self.entries["page.margin_indent"].get().strip()),
                    "space_width_factor": float(self.entries["page.space_width_factor"].get().strip()),
                    "show_rules": bool(self.entries["page.show_rules"].get()),
                    "show_margin": bool(self.entries["page.show_margin"].get()),
                    "rule_line_width": float(self.entries["page.rule_line_width"].get().strip()),
                    "margin_line_width": float(self.entries["page.margin_line_width"].get().strip()),
                },
                "colors": {
                    "rule_line": self.entries["colors.rule_line"].get().strip(),
                    "margin_line": self.entries["colors.margin_line"].get().strip(),
                    "desk": self.parent.cfg.get("colors", {}).get("desk", DESK),
                    "paper": self.parent.cfg.get("colors", {}).get("paper", PAPER),
                    "ink": self.parent.cfg.get("colors", {}).get("ink", INK),
                },
                "database": {
                    "default_path": self.entries["database.default_path"].get().strip(),
                },
            }

            save_config(new_cfg)
            self.parent.apply_config(new_cfg)
            messagebox.showinfo("ScriptForge", "Settings saved successfully!")
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check numeric fields: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {e}")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScriptForge")
        self.geometry("940x620")
        self.minsize(820, 540)

        # Load configuration
        self.cfg = load_config()
        ctk.set_appearance_mode("light")

        self.f_title = ctk.CTkFont(size=26, weight="bold")
        self.f_head = ctk.CTkFont(size=16, weight="bold")
        self.f_body = ctk.CTkFont(size=13)
        self.f_write = ctk.CTkFont(size=16)

        self.profile = None
        self.last_pdf = None
        self.buttons = []
        self.settings_window = None

        self.build_sidebar()
        self.build_page()
        self.setup_editor_shortcuts()

    # Layout

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
        self.side = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=DESK)
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)

        ctk.CTkLabel(self.side, text="ScriptForge", font=self.f_title, text_color=INK
                     ).pack(anchor="w", padx=24, pady=(28, 2))
        ctk.CTkLabel(self.side, text="Turn typed text into your own handwriting.",
                     font=self.f_body, text_color=MUTED, wraplength=250, justify="left"
                     ).pack(anchor="w", padx=24)

        ctk.CTkLabel(self.side, text="Your handwriting", font=self.f_head, text_color=INK
                     ).pack(anchor="w", padx=24, pady=(32, 4))
        ctk.CTkLabel(self.side, text="Upload a photo of the sheet where you wrote a to z, one letter per box.",
                     font=self.f_body, text_color=MUTED, wraplength=250, justify="left"
                     ).pack(anchor="w", padx=24, pady=(0, 12))

        self.make_button(self.side, "Choose sheet photo", self.pick_sheet, primary=True
                         ).pack(fill="x", padx=24)
        self.make_button(self.side, "Use saved profile", self.pick_profile
                         ).pack(fill="x", padx=24, pady=(8, 0))
        self.make_button(self.side, "Save profile as...", self.save_current_profile
                         ).pack(fill="x", padx=24, pady=(8, 0))

        self.hw_label = ctk.CTkLabel(self.side, text="Using the default saved handwriting.",
                                     font=self.f_body, text_color=MUTED,
                                     wraplength=250, justify="left")
        self.hw_label.pack(anchor="w", padx=24, pady=(12, 0))

        # Bottom section: settings & status
        bottom_box = ctk.CTkFrame(self.side, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=24, pady=(0, 20))

        self.status = ctk.CTkLabel(bottom_box, text="Ready.", font=self.f_body, text_color=INK,
                                   wraplength=250, justify="left")
        self.status.pack(anchor="w", pady=(0, 8))

        self.progress = ctk.CTkProgressBar(bottom_box, mode="indeterminate", height=5,
                                           corner_radius=2, fg_color=RULE, progress_color=INK)

        self.make_button(bottom_box, "⚙ Settings", self.open_settings
                         ).pack(fill="x", pady=(6, 0))

    def build_page(self):
        page = ctk.CTkFrame(self, corner_radius=0, fg_color=PAPER)
        page.pack(side="left", fill="both", expand=True)

        self.margin_line = ctk.CTkFrame(
            page, width=2, corner_radius=0,
            fg_color=self.cfg.get("colors", {}).get("margin_line", MARGIN)
        )
        self.margin_line.pack(side="left", fill="y", padx=(44, 0))

        content = ctk.CTkFrame(page, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(20, 28), pady=24)

        # Header with title and "Upload text" button
        head_row = ctk.CTkFrame(content, fg_color="transparent")
        head_row.pack(fill="x")

        ctk.CTkLabel(head_row, text="What to write", font=self.f_head, text_color=INK
                     ).pack(side="left")

        self.make_button(head_row, "Upload text (.txt)", self.upload_text
                         ).pack(side="right")

        self.rule_sep = ctk.CTkFrame(
            content, height=1, corner_radius=0,
            fg_color=self.cfg.get("colors", {}).get("rule_line", RULE)
        )
        self.rule_sep.pack(fill="x", pady=(8, 10))

        self.box = ctk.CTkTextbox(content, font=self.f_write, fg_color=PAPER,
                                  text_color=INK, border_width=0, wrap="word",
                                  undo=True)
        self.box.pack(fill="both", expand=True)
        self.box.focus()

        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x", pady=(14, 0))
        self.make_button(row, "Make PDF", self.make_pdf, primary=True).pack(side="right")
        self.open_btn = self.make_button(row, "Open PDF", self.open_last)

    def setup_editor_shortcuts(self):
        tb = self.box._textbox

        def delete_word_back(event=None):
            try:
                # If there is an active selection, delete the selection
                if tb.tag_ranges("sel"):
                    tb.delete("sel.first", "sel.last")
                    return "break"

                pos = tb.index("insert")
                line, col = map(int, pos.split("."))
                if col == 0:
                    if line > 1:
                        # At start of line: backspace joins with previous line
                        tb.delete(f"{pos} -1c", pos)
                    return "break"

                line_text = tb.get(f"{line}.0", pos)
                # Matches trailing whitespace then word characters or punctuation
                match = re.search(r"(\s+|[^\s\w]+|\w+)\s*$", line_text)
                if match:
                    start_col = match.start()
                    tb.delete(f"{line}.{start_col}", pos)
                else:
                    tb.delete(f"{pos} -1c", pos)
                return "break"
            except Exception:
                return "break"

        def delete_word_forward(event=None):
            try:
                if tb.tag_ranges("sel"):
                    tb.delete("sel.first", "sel.last")
                    return "break"

                pos = tb.index("insert")
                line, col = map(int, pos.split("."))
                line_after = tb.get(pos, f"{line}.end")
                if not line_after:
                    tb.delete(pos, f"{pos} +1c")
                    return "break"

                match = re.match(r"^\s*(\w+|[^\s\w]+|\s+)", line_after)
                if match:
                    end_col = col + match.end()
                    tb.delete(pos, f"{line}.{end_col}")
                else:
                    tb.delete(pos, f"{pos} +1c")
                return "break"
            except Exception:
                return "break"

        def delete_to_line_start(event=None):
            try:
                if tb.tag_ranges("sel"):
                    tb.delete("sel.first", "sel.last")
                    return "break"

                pos = tb.index("insert")
                line, col = map(int, pos.split("."))
                if col == 0 and line > 1:
                    tb.delete(f"{pos} -1c", pos)
                else:
                    tb.delete(f"{line}.0", pos)
                return "break"
            except Exception:
                return "break"

        def on_key_backspace(event):
            # Check for Alt/Option (state bits 0x0008, 0x0010, 0x0080) or Control (0x0004)
            if (event.state & 0x0008) or (event.state & 0x0080) or (event.state & 0x0004) or (event.state & 0x0010):
                return delete_word_back(event)
            return None

        # Bind explicit cross-platform virtual events
        for seq in ("<Alt-BackSpace>", "<Control-BackSpace>", "<Meta-BackSpace>"):
            tb.bind(seq, delete_word_back)
            self.box.bind(seq, delete_word_back)

        # macOS Command+Backspace (delete to start of line)
        tb.bind("<Command-BackSpace>", delete_to_line_start)
        self.box.bind("<Command-BackSpace>", delete_to_line_start)

        # Forward delete word
        for seq in ("<Alt-Delete>", "<Control-Delete>", "<Meta-Delete>"):
            tb.bind(seq, delete_word_forward)
            self.box.bind(seq, delete_word_forward)

        # Catch-all for BackSpace when modifier state is active
        tb.bind("<KeyPress-BackSpace>", on_key_backspace, add="+")

    def apply_config(self, new_cfg: dict):
        """Applies newly saved configuration to GUI elements."""
        self.cfg = new_cfg

        margin_color = new_cfg.get("colors", {}).get("margin_line", MARGIN)
        rule_color = new_cfg.get("colors", {}).get("rule_line", RULE)
        self.margin_line.configure(fg_color=margin_color)
        self.rule_sep.configure(fg_color=rule_color)
        self.status.configure(text="Settings applied.")

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.lift()
            self.settings_window.focus()

    # Button Actions

    def upload_text(self):
        path = filedialog.askopenfilename(
            title="Choose a text file",
            filetypes=[("Text files", "*.txt *.md *.rtf *.text"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            p = Path(path)
            content = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = p.read_text(encoding="latin-1")
            except Exception as err:
                messagebox.showerror("ScriptForge", f"Could not read text file: {err}")
                return
        except Exception as err:
            messagebox.showerror("ScriptForge", f"Could not read text file: {err}")
            return

        curr_text = self.box.get("1.0", "end").strip()
        if curr_text:
            ans = messagebox.askyesnocancel(
                "Upload Text",
                f"Replace existing editor text with '{p.name}'?\n\n"
                "• Yes: Replace current text\n"
                "• No: Append to current text\n"
                "• Cancel: Abort",
            )
            if ans is None:
                return
            if ans:
                self.box.delete("1.0", "end")
                self.box.insert("1.0", content)
            else:
                self.box.insert("end", ("\n\n" if curr_text else "") + content)
        else:
            self.box.delete("1.0", "end")
            self.box.insert("1.0", content)

        self.status.configure(text=f"Loaded text from {p.name}")

    def pick_sheet(self):
        path = filedialog.askopenfilename(
            title="Choose your handwriting sheet",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff"), ("All files", "*.*")],
        )
        if not path:
            return

        # Prompt user if they want to save this handwriting as a profile
        save_opt = messagebox.askyesnocancel(
            "Save Handwriting Profile",
            "Do you want to save this handwriting as a permanent profile (.db) to reuse later?\n\n"
            "• Yes: Save as a named .db profile\n"
            "• No: Use directly for this session (saved to default profile)\n"
            "• Cancel: Abort",
        )
        if save_opt is None:
            return

        target_db = None
        if save_opt:
            target_db = filedialog.asksaveasfilename(
                title="Save Handwriting Profile As",
                defaultextension=".db",
                filetypes=[("Handwriting profile", "*.db")],
                initialfile="my_handwriting.db",
            )
            if not target_db:
                return

        self.run_in_background(
            work=lambda: extract_glyphs(path, name=target_db),
            busy="Reading sheet",
            done=lambda: self.sheet_done(path, target_db),
        )

    def sheet_done(self, img_path: str, profile_path: str | None = None):
        if profile_path:
            self.profile = profile_path
            self.hw_label.configure(text=f"Using {Path(profile_path).name}")
            self.status.configure(text=f"Profile saved: {Path(profile_path).name}")
        else:
            self.profile = None
            self.hw_label.configure(text=f"Learned from {Path(img_path).name}")
            self.status.configure(text="Sheet read into default profile. Type something and make a PDF.")

    def pick_profile(self):
        path = filedialog.askopenfilename(
            title="Choose a saved profile",
            filetypes=[("Handwriting profile", "*.db")],
        )
        if not path:
            return
        self.profile = path
        self.hw_label.configure(text=f"Using {Path(path).name}")
        self.status.configure(text="Profile loaded.")

    def save_current_profile(self):
        """Allows exporting or saving the current active handwriting as a .db profile."""
        default_db = Path(self.cfg.get("database", {}).get("default_path", ".bin/default.db"))
        source = Path(self.profile) if self.profile else default_db

        if not source.exists():
            messagebox.showinfo(
                "ScriptForge",
                "No handwriting profile found yet. Please choose a sheet photo to extract first.",
            )
            return

        dest = filedialog.asksaveasfilename(
            title="Save Profile As",
            defaultextension=".db",
            filetypes=[("Handwriting profile", "*.db")],
            initialfile=source.name if source != default_db else "my_handwriting.db",
        )
        if not dest:
            return

        try:
            shutil.copy2(source, dest)
            self.profile = dest
            self.hw_label.configure(text=f"Using {Path(dest).name}")
            self.status.configure(text=f"Profile saved: {Path(dest).name}")
            messagebox.showinfo("ScriptForge", f"Profile saved to:\n{dest}")
        except Exception as err:
            messagebox.showerror("ScriptForge", f"Could not save profile: {err}")

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
            work=lambda: generate_pdf(str(txt), out, profile, cfg=self.cfg),
            busy="Making PDF",
            done=lambda: self.pdf_done(out),
        )

    def open_last(self):
        if self.last_pdf:
            open_file(self.last_pdf)

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
