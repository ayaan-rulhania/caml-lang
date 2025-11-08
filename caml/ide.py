import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os
import re

# -------- Configuration --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMLSCRIPT = os.path.join(BASE_DIR, "caml-code", "run_caml.py")
CAMEL_ACCENT = "#C19A6B"  # requested accent
BG = "#f5f5f7"
TAB_BG = "#ffffff"
LINE_BG = "#f0f0f0"

# A lightweight set of Caml/OCaml keywords for highlighting — expand as needed
CAML_KEYWORDS = [
    "let", "in", "rec", "match", "with", "type", "module", "open", "fun",
    "if", "then", "else", "begin", "end", "and", "or", "not", "as"
]
KEYWORD_RE = r"\b(" + r"|".join(re.escape(w) for w in CAML_KEYWORDS) + r")\b"
STRING_RE = r'".*?"|\'.*?\''
COMMENT_RE = r"\(\*.*?\*\)"  # non-greedy DOTALL match
NUMBER_RE = r"\b\d+(\.\d+)?\b"

HIGHLIGHT_DELAY_MS = 200  # debounce for highlighting

# -------- Helper / Tab management --------
def make_tab_title(filename):
    """Show 'name  ×' so tabs visually show a close marker."""
    return f"{filename}  ×"

def basename_or_untitled(path):
    return os.path.basename(path) if path else "Untitled"


# -------- UI Functions --------
def create_editor_frame(file_path=None, content=""):
    """Create editor frame with line numbers and Text widget. Store metadata on frame."""
    frame = tk.Frame(notebook, bg=TAB_BG)
    frame.file_path = file_path  # attribute to remember file location
    frame.highlight_after_id = None

    # Left: line numbers
    ln_frame = tk.Frame(frame, bg=LINE_BG)
    ln_frame.pack(side=tk.LEFT, fill=tk.Y)

    ln_text = tk.Text(ln_frame, width=4, bg=LINE_BG, fg="#666666",
                      font=("Menlo", 12), bd=0, padx=4, pady=4, state='disabled')
    ln_text.pack(fill=tk.Y, expand=True)

    # Right: editor area
    text_widget = tk.Text(frame, bg="#fefefe", fg="#1c1c1e",
                          font=("Menlo", 12), bd=0, padx=10, pady=8, wrap="none", undo=True)
    text_widget.insert("1.0", content)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Scrollbar shared between ln_text and text_widget
    vsb = tk.Scrollbar(text_widget)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    vsb.config(command=lambda *args: (text_widget.yview(*args), ln_text.yview(*args)))
    text_widget.config(yscrollcommand=vsb.set)
    ln_text.config(yscrollcommand=vsb.set)

    # Bindings to update line numbers and highlighting
    def schedule_update(event=None):
        # update line numbers immediately but debounce highlight
        update_line_numbers()
        if frame.highlight_after_id:
            text_widget.after_cancel(frame.highlight_after_id)
        frame.highlight_after_id = text_widget.after(HIGHLIGHT_DELAY_MS, lambda: highlight_syntax(text_widget))

    text_widget.bind("<KeyRelease>", schedule_update)
    text_widget.bind("<ButtonRelease-1>", schedule_update)
    text_widget.bind("<MouseWheel>", lambda e: (ln_text.yview_scroll(int(-1*(e.delta/120)), "units")))
    text_widget.bind("<Configure>", lambda e: schedule_update())

    # initial line numbers & highlighting
    update_line_numbers_for_widget(text_widget, ln_text)
    highlight_syntax(text_widget)

    # Attach widgets as metadata so other functions can find them
    frame.text_widget = text_widget
    frame.ln_text = ln_text

    return frame


def update_line_numbers_for_widget(text_widget, ln_text):
    ln_text.config(state='normal')
    ln_text.delete("1.0", tk.END)
    text = text_widget.get("1.0", "end-1c")
    lines = text.split("\n")
    for i in range(1, len(lines) + 1):
        ln_text.insert(tk.END, f"{i}\n")
    ln_text.config(state='disabled')


def update_line_numbers():
    """Update line numbers for the currently selected tab."""
    try:
        current = notebook.nametowidget(notebook.select())
    except Exception:
        return
    if not hasattr(current, "text_widget"):
        return
    update_line_numbers_for_widget(current.text_widget, current.ln_text)


# -------- Syntax highlighting --------
def remove_all_tags(text_widget):
    for tag in ("kw", "str", "comment", "num"):
        text_widget.tag_remove(tag, "1.0", tk.END)


def highlight_syntax(text_widget):
    """Simple regex-based highlighter — works on the whole buffer."""
    remove_all_tags(text_widget)
    code = text_widget.get("1.0", "end-1c")

    # comments (DOTALL)
    for m in re.finditer(COMMENT_RE, code, re.DOTALL):
        start = index_from_pos(code, m.start())
        end = index_from_pos(code, m.end())
        text_widget.tag_add("comment", start, end)

    # strings
    for m in re.finditer(STRING_RE, code):
        start = index_from_pos(code, m.start())
        end = index_from_pos(code, m.end())
        text_widget.tag_add("str", start, end)

    # numbers
    for m in re.finditer(NUMBER_RE, code):
        # avoid tagging numbers inside strings/comments by checking current tags
        start = index_from_pos(code, m.start())
        end = index_from_pos(code, m.end())
        if not text_widget.tag_names(start):
            text_widget.tag_add("num", start, end)

    # keywords (avoid matches inside strings/comments by checking tag ranges)
    for m in re.finditer(KEYWORD_RE, code):
        start = index_from_pos(code, m.start())
        end = index_from_pos(code, m.end())
        # if start is inside a string or comment, skip
        overlapping = False
        for tag in ("str", "comment"):
            ranges = text_widget.tag_ranges(tag)
            for i in range(0, len(ranges), 2):
                rstart = ranges[i]
                rend = ranges[i+1]
                if text_widget.compare(start, ">=", rstart) and text_widget.compare(start, "<", rend):
                    overlapping = True
                    break
            if overlapping:
                break
        if not overlapping:
            text_widget.tag_add("kw", start, end)

    # configure tags (colors)
    text_widget.tag_configure("kw", foreground=CAMEL_ACCENT, font=("Menlo", 12, "bold"))
    text_widget.tag_configure("str", foreground="#2a9d8f")      # strings: teal-ish
    text_widget.tag_configure("comment", foreground="#9aa0a6", font=("Menlo", 12, "italic"))
    text_widget.tag_configure("num", foreground="#3b82f6")      # numbers: blue


def index_from_pos(text, pos):
    """Return Tk text index string from character offset pos in 'text'."""
    # Count lines and columns
    lines = text[:pos].splitlines()
    if not lines:
        row = 1
        col = pos
    else:
        row = len(lines)
        col = len(lines[-1])
    return f"{row}.{col}"


# -------- File operations and run --------
def new_tab(file_path=None, content=""):
    """Create new tab before the '+' tab; if '+' doesn't exist, just add."""
    frame = create_editor_frame(file_path=file_path, content=content)
    title = basename_or_untitled(file_path)
    tab_title = make_tab_title(title)

    # Insert before '+' if plus exists
    if notebook.index("end") > 0 and notebook.tab(notebook.index("end")-1, "text") == "+":
        notebook.insert(notebook.index("end")-1, frame, text=tab_title)
    else:
        notebook.add(frame, text=tab_title)
    notebook.select(frame)
    return frame


def open_file():
    path = filedialog.askopenfilename(
        filetypes=[("Caml files", "*.caml"), ("Python files", "*.py"), ("All files", "*.*")]
    )
    if not path:
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    frame = new_tab(file_path=path, content=content)
    frame.file_path = path
    # update title to file basename
    idx = notebook.index(frame)
    notebook.tab(idx, text=make_tab_title(os.path.basename(path)))
    # run highlighting immediately
    highlight_syntax(frame.text_widget)
    update_line_numbers_for_widget(frame.text_widget, frame.ln_text)


def save_file(save_as=False):
    """Save the currently selected tab. If save_as or no path defined -> asksaveas."""
    try:
        current = notebook.nametowidget(notebook.select())
    except Exception:
        return None
    if not hasattr(current, "text_widget"):
        return None
    text_widget = current.text_widget
    if not save_as and getattr(current, "file_path", None):
        path = current.file_path
    else:
        path = filedialog.asksaveasfilename(defaultextension=".caml", filetypes=[("Caml files", "*.caml")])
        if not path:
            return None
    with open(path, "w", encoding="utf-8") as f:
        f.write(text_widget.get("1.0", "end-1c"))
    current.file_path = path
    # update title
    idx = notebook.index(current)
    notebook.tab(idx, text=make_tab_title(os.path.basename(path)))
    return path


def run_file():
    """Save (if needed) then run the file via CAMLSCRIPT."""
    try:
        current = notebook.nametowidget(notebook.select())
    except Exception:
        messagebox.showinfo("No tab", "No tab selected.")
        return
    if not hasattr(current, "text_widget"):
        messagebox.showinfo("No editor", "Nothing to run.")
        return
    text_widget = current.text_widget
    # save if file_path not defined
    path = save_file(save_as=False)
    if not path:
        return
    if not os.path.isfile(CAMLSCRIPT):
        messagebox.showerror("Error", f"Caml runner script not found:\n{CAMLSCRIPT}")
        return
    try:
        output = subprocess.check_output([sys.executable, CAMLSCRIPT, path], stderr=subprocess.STDOUT, text=True)
        set_output(output)
    except subprocess.CalledProcessError as e:
        set_output(e.output)
        messagebox.showerror("Execution Error", "Error running Caml script. See output below.")


def set_output(text):
    output_area.config(state='normal')
    output_area.delete("1.0", tk.END)
    output_area.insert("1.0", text)
    output_area.config(state='disabled')


# -------- Tab click/close behavior --------
def on_tab_changed(event):
    """If user clicked the '+' tab, create a new tab."""
    sel = notebook.index("current")
    try:
        if notebook.tab(sel, "text") == "+":
            new_tab()
            # select the newly created tab (placed before '+')
            notebook.select(notebook.index("end") - 2)
    except Exception:
        pass
    update_line_numbers()


def on_tab_click(event):
    """Detect click on tab label; if clicked near right edge of tab label, close it."""
    # compute which tab was clicked
    try:
        tab_id = notebook.index("@%d,%d" % (event.x, event.y))
    except Exception:
        return
    try:
        bbox = notebook.bbox(tab_id)  # (x,y,w,h)
    except Exception:
        return
    if not bbox:
        return
    x, y, w, h = bbox
    # if click is within ~20px of right edge, treat as close click
    close_thresh = 20
    if event.x >= x + w - close_thresh:
        # do not close plus tab
        if notebook.tab(tab_id, "text") == "+":
            return
        notebook.forget(tab_id)
    else:
        # normal tab selection (default)
        notebook.select(tab_id)


# -------- UI Build --------
root = tk.Tk()
root.title("Caml IDE")
root.geometry("1200x800")
root.configure(bg=BG)

# top container: notebook on left, action buttons on right (so buttons visually align with tab row)
top_container = tk.Frame(root, bg=BG)
top_container.pack(fill=tk.X, padx=18, pady=(18, 4))

# Notebook frame (to set height)
notebook_frame = tk.Frame(top_container, bg=BG)
notebook_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

style = ttk.Style()
style.theme_use("default")
style.configure("TNotebook", background=BG, borderwidth=0)
style.configure("TNotebook.Tab", background=TAB_BG, padding=[12, 8], font=("Helvetica", 11, "bold"))
style.map("TNotebook.Tab", background=[("selected", CAMEL_ACCENT)], foreground=[("selected", "white")])

notebook = ttk.Notebook(notebook_frame)
notebook.pack(fill=tk.X, expand=True)

notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
notebook.bind("<Button-1>", on_tab_click)

# Add initial tab using add() (so we have an 'end' index), then add the '+' tab
first_frame = create_editor_frame()
notebook.add(first_frame, text=make_tab_title("Untitled"))
# add '+' tab on the far right
plus_frame = tk.Frame(notebook, bg=TAB_BG)
notebook.add(plus_frame, text="+")

# Right-side action buttons that visually match tabs
btn_frame = tk.Frame(top_container, bg=BG)
btn_frame.pack(side=tk.RIGHT, padx=(6, 18))

def make_tab_like_button(text, command):
    btn = tk.Button(btn_frame, text=text, command=command, bd=0, padx=12, pady=6,
                    font=("Helvetica", 11, "bold"), relief="flat", bg=TAB_BG, activebackground="#efe6de")
    # style hover/active appearance to resemble tab selection
    def on_enter(e):
        btn.config(bg="#f2ebe3")
    def on_leave(e):
        btn.config(bg=TAB_BG)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn

open_btn = make_tab_like_button("Open", open_file)
open_btn.pack(side=tk.TOP, pady=0)

run_btn = make_tab_like_button("Run", run_file)
run_btn.pack(side=tk.TOP, pady=(6,0))

# Output area below
output_frame = tk.Frame(root, bg="#fefefe", bd=1, relief="solid")
output_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(6, 18))

output_label = tk.Label(output_frame, text="Output", bg="#fefefe", fg="#333333",
                        font=("Helvetica", 14, "bold"))
output_label.pack(anchor="w", padx=10, pady=(6, 0))

output_area = tk.Text(output_frame, height=12, bg="#fdfdfd", fg="#1c1c1e",
                      font=("Menlo", 12), bd=0, padx=10, pady=10, state='disabled', wrap="none")
output_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

# Key shortcuts
root.bind("<Control-r>", lambda e: run_file())
root.bind("<Control-o>", lambda e: open_file())
root.bind("<Control-s>", lambda e: save_file())

# initial highlight config for first tab's text widget
highlight_syntax(first_frame.text_widget)
first_frame.ln_text.config(state='normal')
update_line_numbers_for_widget(first_frame.text_widget, first_frame.ln_text)
first_frame.ln_text.config(state='disabled')

root.mainloop()
