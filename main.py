import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter.font as tkfont
from typing import Optional


class NoteApp:
    """A simple GUI note taking app using Tkinter."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Note — Untitled")
        self.root.geometry("900x700")

        self.current_file_path: Optional[str] = None
        self.is_modified: bool = False

        # UI state
        self.theme_mode: str = "light"
        self.wrap_enabled_var = tk.BooleanVar(value=True)
        self.show_line_numbers_var = tk.BooleanVar(value=True)

        self._init_style()
        self._configure_fonts()
        self._create_widgets()
        self._apply_theme()
        self._create_menu()
        self._create_bindings()
        self._update_status_bar()

    def _create_widgets(self) -> None:
        # Toolbar
        self.toolbar = ttk.Frame(self.root, padding=(8, 6))
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Some Tk builds/fonts don't render emoji well; use plain text labels for portability
        self.btn_new = ttk.Button(self.toolbar, text="New", width=8, command=self.new_file)
        self.btn_open = ttk.Button(self.toolbar, text="Open", width=8, command=self.open_file)
        self.btn_save = ttk.Button(self.toolbar, text="Save", width=8, command=self.save_file)
        self.btn_find = ttk.Button(self.toolbar, text="Find", width=8, command=self.open_find_dialog)
        self.btn_theme = ttk.Button(self.toolbar, text="Dark", width=10, command=self.toggle_theme)
        for w in (self.btn_new, self.btn_open, self.btn_save, self.btn_find, self.btn_theme):
            w.pack(side=tk.LEFT, padx=(0, 6))

        # Main content area
        self.main_frame = ttk.Frame(self.root, padding=(8, 0, 8, 0))
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Line numbers gutter
        self.line_numbers_canvas = tk.Canvas(self.content_frame, width=48, highlightthickness=0)
        self.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y)

        # Text area + scrollbar
        self.scrollbar_y = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL)
        self.text_area = tk.Text(
            self.content_frame,
            wrap=tk.WORD,
            undo=True,
            autoseparators=True,
            maxundo=-1,
            yscrollcommand=self._on_yscroll,
            padx=12,
            pady=12,
        )
        self.text_area.configure(spacing1=4, spacing3=6, insertwidth=2)
        self.scrollbar_y.config(command=self.text_area.yview)

        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Status bar (segmented)
        self.status_var = tk.StringVar(value="Ready")
        self.status_right_var = tk.StringVar(value="")
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            anchor=tk.W,
            relief=tk.SUNKEN,
            bd=1,
            padx=10,
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_bar_right = tk.Label(
            self.status_frame,
            textvariable=self.status_right_var,
            anchor=tk.E,
            relief=tk.SUNKEN,
            bd=1,
            padx=10,
        )
        self.status_bar_right.pack(side=tk.RIGHT)

        # Text tags
        self.text_area.tag_configure("find_match", background="#ffea94")
        self.text_area.tag_configure("current_line", background="")

    def _create_menu(self) -> None:
        self.menubar = tk.Menu(self.root)

        file_menu = tk.Menu(self.menubar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open…", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As…", accelerator="Ctrl+Shift+S", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.on_exit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(self.menubar, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=lambda: self._event_generate_and_focus("<Control-z>"))
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=lambda: self._event_generate_and_focus("<Control-y>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self._event_generate_and_focus("<Control-x>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self._event_generate_and_focus("<Control-c>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self._event_generate_and_focus("<Control-v>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=lambda: self._event_generate_and_focus("<Control-a>"))
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        search_menu = tk.Menu(self.menubar, tearoff=False)
        search_menu.add_command(label="Find…", accelerator="Ctrl+F", command=self.open_find_dialog)
        self.menubar.add_cascade(label="Search", menu=search_menu)

        view_menu = tk.Menu(self.menubar, tearoff=False)
        view_menu.add_checkbutton(
            label="Word Wrap",
            onvalue=True,
            offvalue=False,
            variable=self.wrap_enabled_var,
            command=self.toggle_wrap,
        )
        view_menu.add_checkbutton(
            label="Show Line Numbers",
            onvalue=True,
            offvalue=False,
            variable=self.show_line_numbers_var,
            command=self.toggle_line_numbers,
        )
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Theme", accelerator="Ctrl+T", command=self.toggle_theme)
        self.menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(self.menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar)

    def _create_bindings(self) -> None:
        self.root.bind("<Control-n>", lambda e: self._wrap_event(self.new_file))
        self.root.bind("<Control-o>", lambda e: self._wrap_event(self.open_file))
        self.root.bind("<Control-s>", lambda e: self._wrap_event(self.save_file))
        self.root.bind("<Control-S>", lambda e: self._wrap_event(self.save_file_as))
        self.root.bind("<Control-q>", lambda e: self._wrap_event(self.on_exit))
        self.root.bind("<Control-f>", lambda e: self._wrap_event(self.open_find_dialog))
        self.root.bind("<Control-t>", lambda e: self._wrap_event(self.toggle_theme))

        # Zoom text
        self.root.bind("<Control-minus>", lambda e: self._wrap_event(lambda: self._adjust_font_size(-1)))
        self.root.bind("<Control-equal>", lambda e: self._wrap_event(lambda: self._adjust_font_size(+1)))
        self.root.bind("<Control-underscore>", lambda e: self._wrap_event(lambda: self._adjust_font_size(-1)))
        self.root.bind("<Control-plus>", lambda e: self._wrap_event(lambda: self._adjust_font_size(+1)))

        self.text_area.bind("<<Modified>>", self._on_text_modified)
        self.text_area.bind("<KeyRelease>", self._on_cursor_or_view_changed)
        self.text_area.bind("<ButtonRelease-1>", self._on_cursor_or_view_changed)
        self.text_area.bind("<MouseWheel>", self._on_cursor_or_view_changed)
        self.text_area.bind("<Button-4>", self._on_cursor_or_view_changed)
        self.text_area.bind("<Button-5>", self._on_cursor_or_view_changed)
        self.text_area.bind("<Configure>", self._on_cursor_or_view_changed)

        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def _wrap_event(self, fn):
        fn()
        return "break"

    def _event_generate_and_focus(self, sequence: str) -> None:
        self.text_area.event_generate(sequence)
        self.text_area.focus_set()

    def _on_text_modified(self, event=None) -> None:
        if self.text_area.edit_modified():
            self.is_modified = True
            self._update_window_title()
            self._update_status_bar()
            self._highlight_current_line()
            self._update_line_numbers()
            self.text_area.edit_modified(False)

    def _update_window_title(self) -> None:
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
        modified_marker = "*" if self.is_modified else ""
        self.root.title(f"Note — {filename}{modified_marker}")

    def _update_status_bar(self, event=None) -> None:
        index = self.text_area.index("insert")
        line_str, col_str = index.split(".")
        modified_label = "Modified" if self.is_modified else "Saved"
        content = self.text_area.get("1.0", "end-1c")
        char_count = len(content)
        word_count = len(content.split()) if content else 0
        try:
            sel_length = len(self.text_area.get("sel.first", "sel.last"))
        except tk.TclError:
            sel_length = 0
        sel_part = f" | Sel {sel_length}" if sel_length else ""
        left = f"{modified_label} | Ln {int(line_str)}, Col {int(col_str) + 1}{sel_part}"
        right = f"{char_count} chars | {word_count} words"
        self.status_var.set(left)
        self.status_right_var.set(right)

    def maybe_save_changes(self) -> bool:
        if not self.is_modified:
            return True
        response = messagebox.askyesnocancel("Save changes?", "Your notes have unsaved changes. Save now?")
        if response is None:
            return False
        if response:
            return self.save_file()
        return True

    def new_file(self) -> None:
        if not self.maybe_save_changes():
            return
        self.text_area.delete("1.0", tk.END)
        self.current_file_path = None
        self.is_modified = False
        self.text_area.edit_reset()
        self._update_window_title()
        self._update_status_bar()
        self._clear_find_highlights()
        self._highlight_current_line()
        self._update_line_numbers()

    def open_file(self) -> None:
        if not self.maybe_save_changes():
            return
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Markdown", "*.md"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            messagebox.showerror("Open Failed", f"Could not open file.\n\n{exc}")
            return
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", content)
        self.current_file_path = file_path
        self.is_modified = False
        self.text_area.edit_reset()
        self._clear_find_highlights()
        self._update_window_title()
        self._update_status_bar()
        self._highlight_current_line()
        self._update_line_numbers()

    def save_file(self) -> bool:
        if self.current_file_path is None:
            return self.save_file_as()
        try:
            content = self.text_area.get("1.0", tk.END)
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(content.rstrip("\n"))
                f.write("\n")
        except Exception as exc:
            messagebox.showerror("Save Failed", f"Could not save file.\n\n{exc}")
            return False
        self.is_modified = False
        self._update_window_title()
        self._update_status_bar()
        return True

    def save_file_as(self) -> bool:
        initial_dir = os.path.dirname(self.current_file_path) if self.current_file_path else os.getcwd()
        file_path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            initialdir=initial_dir,
            filetypes=[
                ("Text Files", "*.txt"),
                ("Markdown", "*.md"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return False
        self.current_file_path = file_path
        return self.save_file()

    def on_exit(self) -> None:
        if not self.maybe_save_changes():
            return
        self.root.destroy()

    def open_find_dialog(self) -> None:
        if hasattr(self, "find_window") and self.find_window.winfo_exists():
            self.find_window.lift()
            return
        self.find_window = tk.Toplevel(self.root)
        self.find_window.title("Find")
        self.find_window.transient(self.root)
        self.find_window.resizable(False, False)
        self.find_window.geometry("360x120")

        label = tk.Label(self.find_window, text="Find text:")
        label.pack(anchor=tk.W, padx=10, pady=(10, 0))

        entry_frame = tk.Frame(self.find_window)
        entry_frame.pack(fill=tk.X, padx=10, pady=6)
        self.find_var = tk.StringVar()
        entry = tk.Entry(entry_frame, textvariable=self.find_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        buttons = tk.Frame(self.find_window)
        buttons.pack(fill=tk.X, padx=10, pady=(0, 10))
        btn_find = tk.Button(buttons, text="Find Next", width=12, command=self._find_next)
        btn_all = tk.Button(buttons, text="Highlight All", width=12, command=self._highlight_all)
        btn_clear = tk.Button(buttons, text="Clear", width=8, command=self._clear_find_highlights)
        btn_find.pack(side=tk.LEFT)
        btn_all.pack(side=tk.LEFT, padx=6)
        btn_clear.pack(side=tk.LEFT)

        entry.bind("<Return>", lambda e: self._find_next())
        entry.focus_set()

    def _clear_find_highlights(self) -> None:
        self.text_area.tag_remove("find_match", "1.0", tk.END)

    def _find_next(self) -> None:
        pattern = (self.find_var.get() if hasattr(self, "find_var") else "").strip()
        if not pattern:
            return
        start_index = self.text_area.index(tk.INSERT)
        match_index = self.text_area.search(pattern, start_index, stopindex=tk.END, nocase=True)
        if not match_index:
            wrap_index = self.text_area.search(pattern, "1.0", stopindex=start_index, nocase=True)
            if not wrap_index:
                self.root.bell()
                return
            match_index = wrap_index
        end_index = f"{match_index}+{len(pattern)}c"
        self.text_area.tag_remove("sel", "1.0", tk.END)
        self.text_area.tag_add("sel", match_index, end_index)
        self.text_area.see(match_index)
        self.text_area.mark_set(tk.INSERT, end_index)
        self.text_area.focus_set()

    def _highlight_all(self) -> None:
        pattern = (self.find_var.get() if hasattr(self, "find_var") else "").strip()
        if not pattern:
            return
        self._clear_find_highlights()
        start = "1.0"
        while True:
            match_index = self.text_area.search(pattern, start, stopindex=tk.END, nocase=True)
            if not match_index:
                break
            end_index = f"{match_index}+{len(pattern)}c"
            self.text_area.tag_add("find_match", match_index, end_index)
            start = end_index

    def show_about_dialog(self) -> None:
        if hasattr(self, "about_window") and self.about_window.winfo_exists():
            self.about_window.lift()
            return

        self.about_window = tk.Toplevel(self.root)
        self.about_window.title("About — Note")
        self.about_window.transient(self.root)
        self.about_window.resizable(False, False)
        try:
            self.about_window.grab_set()
        except Exception:
            pass

        container = ttk.Frame(self.about_window, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        title_font = tkfont.Font(family=self.ui_font.actual("family"), size=16, weight="bold")
        subtitle_font = tkfont.Font(family=self.ui_font.actual("family"), size=11)

        ttk.Label(container, text="Note", font=title_font).pack(anchor=tk.W)
        ttk.Label(
            container,
            text="A clean, modern note‑taking app built with Python and Tkinter",
            font=subtitle_font,
        ).pack(anchor=tk.W, pady=(2, 10))

        ttk.Separator(container).pack(fill=tk.X, pady=(0, 12))

        about_text = (
            "What it is\n"
            "Note is a lightweight, distraction‑free text editor for quick notes and writing. "
            "It focuses on clarity and comfort: word wrap, line numbers, refined light/dark themes, and a clear status bar.\n\n"
            "How it’s built\n"
            "- Python’s Tkinter for the GUI, with ttk widgets for a native look\n"
            "- A custom theme system (light/dark) applied to widgets\n"
            "- A canvas‑based line‑number gutter synchronized with the Text widget\n"
            "- Find with in‑document highlighting via Text tags\n"
            "- A segmented status bar with cursor position, selection size, and counts\n\n"
            "Key features\n"
            "- New/Open/Save/Save As with unsaved‑changes prompts\n"
            "- Undo/Redo, Cut/Copy/Paste, Select All\n"
            "- Find, Highlight All, Clear highlights\n"
            "- Toggle theme (Ctrl+T), Word Wrap, Line Numbers\n"
            "- Zoom text (Ctrl+= / Ctrl+-)\n"
        )

        # Use Message widget for nice wrapped paragraphs
        msg = tk.Message(container, text=about_text, width=560, anchor=tk.W, justify=tk.LEFT)
        msg.pack(fill=tk.X)

        ttk.Separator(container).pack(fill=tk.X, pady=(12, 10))

        btn_row = ttk.Frame(container)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="Close", command=self.about_window.destroy).pack(side=tk.RIGHT)

        self.about_window.bind("<Escape>", lambda e: self.about_window.destroy())

    # ---- Theming & UI helpers ----
    def _init_style(self) -> None:
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

    def _configure_fonts(self) -> None:
        self.ui_font = tkfont.nametofont("TkDefaultFont")
        self.ui_font.configure(size=11)
        self.text_font = tkfont.nametofont("TkTextFont")
        self.text_font.configure(size=12)

    def _apply_theme(self) -> None:
        if self.theme_mode == "dark":
            bg = "#111827"
            fg = "#e5e7eb"
            panel_bg = "#0b1220"
            gutter_bg = "#0f172a"
            gutter_fg = "#94a3b8"
            insert = "#60a5fa"
            select_bg = "#374151"
            status_bg = "#111827"
            status_fg = "#9ca3af"
            current_line_bg = "#111c2e"
        else:
            bg = "#ffffff"
            fg = "#1f2937"
            panel_bg = "#f8fafc"
            gutter_bg = "#eef2f7"
            gutter_fg = "#64748b"
            insert = "#2563eb"
            select_bg = "#dbeafe"
            status_bg = "#f8fafc"
            status_fg = "#6b7280"
            current_line_bg = "#f7fbff"

        # ttk styles
        for style_name in ("TFrame", "TLabel", "TButton"):
            self.style.configure(style_name, background=panel_bg, foreground=fg)
        self.style.configure("Vertical.TScrollbar", troughcolor=panel_bg)
        self.style.configure("TButton", padding=(8, 4))
        self.style.map(
            "TButton",
            relief=[("pressed", "sunken"), ("!pressed", "flat")],
            focuscolor=[("focus", panel_bg)],
        )

        # Containers
        self.root.configure(background=panel_bg)
        self.toolbar.configure(style="TFrame")
        self.main_frame.configure(style="TFrame")
        self.content_frame.configure(style="TFrame")

        # Text widget
        self.text_area.configure(
            bg=bg,
            fg=fg,
            insertbackground=insert,
            selectbackground=select_bg,
            highlightthickness=1,
            highlightbackground=gutter_bg,
            font=self.text_font,
            wrap=tk.WORD if self.wrap_enabled_var.get() else tk.NONE,
        )
        # Gutter
        self.line_numbers_canvas.configure(background=gutter_bg)
        self.gutter_fg = gutter_fg

        # Status bar
        self.status_frame.configure(style="TFrame")
        self.status_bar.configure(background=status_bg, foreground=status_fg)
        self.status_bar_right.configure(background=status_bg, foreground=status_fg)

        # Current line highlight
        self.text_area.tag_configure("current_line", background=current_line_bg)
        self._highlight_current_line()
        self._update_line_numbers()

        # Toolbar theme button label (plain text for portability)
        self.btn_theme.configure(text=("Light" if self.theme_mode == "dark" else "Dark"))

    def toggle_theme(self) -> None:
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        self._apply_theme()

    def toggle_wrap(self) -> None:
        self.text_area.configure(wrap=tk.WORD if self.wrap_enabled_var.get() else tk.NONE)
        self._apply_theme()

    def toggle_line_numbers(self) -> None:
        if self.show_line_numbers_var.get():
            self.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y)
            self._update_line_numbers()
        else:
            self.line_numbers_canvas.pack_forget()

    def _on_yscroll(self, first: str, last: str) -> None:
        self.scrollbar_y.set(first, last)
        self._update_line_numbers()

    def _on_cursor_or_view_changed(self, event=None) -> None:
        self._highlight_current_line()
        self._update_line_numbers()
        self._update_status_bar()

    def _highlight_current_line(self) -> None:
        self.text_area.tag_remove("current_line", 1.0, tk.END)
        index = self.text_area.index("insert linestart")
        self.text_area.tag_add("current_line", index, f"{index} lineend+1c")

    def _update_line_numbers(self) -> None:
        if not self.show_line_numbers_var.get():
            return
        self.line_numbers_canvas.delete("all")
        try:
            i = self.text_area.index("@0,0")
        except tk.TclError:
            return
        while True:
            dline = self.text_area.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            line = i.split(".")[0]
            self.line_numbers_canvas.create_text(
                44, y + 2, anchor="ne", text=line, fill=self.gutter_fg, font=self.ui_font
            )
            try:
                i = self.text_area.index(f"{i}+1line")
            except tk.TclError:
                break

    def _adjust_font_size(self, delta: int) -> None:
        size = max(8, min(28, self.text_font.cget("size") + delta))
        self.text_font.configure(size=size)
        self._apply_theme()


def main() -> None:
    root = tk.Tk()
    NoteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
