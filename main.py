import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional


class NoteApp:
    """A simple GUI note taking app using Tkinter."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Note — Untitled")
        self.root.geometry("900x700")

        self.current_file_path: Optional[str] = None
        self.is_modified: bool = False

        self._create_widgets()
        self._create_menu()
        self._create_bindings()
        self._update_status_bar()

    def _create_widgets(self) -> None:
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.scrollbar_y = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL)
        self.text_area = tk.Text(
            self.main_frame,
            wrap=tk.WORD,
            undo=True,
            autoseparators=True,
            maxundo=-1,
            yscrollcommand=self.scrollbar_y.set,
        )
        self.scrollbar_y.config(command=self.text_area.yview)

        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor=tk.W,
            relief=tk.SUNKEN,
            bd=1,
            padx=8,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.text_area.tag_configure("find_match", background="#ffea94")

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

        self.text_area.bind("<<Modified>>", self._on_text_modified)
        self.text_area.bind("<KeyRelease>", self._update_status_bar)
        self.text_area.bind("<ButtonRelease-1>", self._update_status_bar)

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
            self.text_area.edit_modified(False)

    def _update_window_title(self) -> None:
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
        modified_marker = "*" if self.is_modified else ""
        self.root.title(f"Note — {filename}{modified_marker}")

    def _update_status_bar(self, event=None) -> None:
        index = self.text_area.index("insert")
        line_str, col_str = index.split(".")
        modified_label = "Modified" if self.is_modified else "Saved"
        self.status_var.set(f"{modified_label}  |  Line {int(line_str)}, Col {int(col_str) + 1}")

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
        app_name = "Note"
        info = (
            f"{app_name}\n"
            "A simple Tkinter note taking app.\n\n"
            "Shortcuts:\n"
            " - Ctrl+N: New\n"
            " - Ctrl+O: Open\n"
            " - Ctrl+S: Save\n"
            " - Ctrl+Shift+S: Save As\n"
            " - Ctrl+F: Find\n"
            " - Ctrl+Q: Exit"
        )
        messagebox.showinfo("About", info, parent=self.root)


def main() -> None:
    root = tk.Tk()
    NoteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
