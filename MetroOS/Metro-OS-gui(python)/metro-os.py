#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metro OS – Tkinter Edition (fixed)
- DEVMODE and CD pages lazy-loaded (created only when requested)
- No Toplevel created automatically; all pages are frames inside main window
- Clean imports and small fixes
"""
from __future__ import annotations
import os
import math
import platform
import socket
import getpass
import time
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

# --------------------------- Paths & Globals --------------------------- #
BASE = Path(__file__).resolve().parent
G_DIR = BASE / "G"
DATA_DIR = G_DIR / "systemfile" / "data"
NEWS_DIR = G_DIR / "News"
PASS_DIR = G_DIR / "pass"
PASS_FILE = PASS_DIR / "password.txt"
CD_DIR = G_DIR / "CD"

DEV_PASSWORD = "10122009"

for p in [DATA_DIR, NEWS_DIR, PASS_DIR, CD_DIR]:
    p.mkdir(parents=True, exist_ok=True)

if not PASS_FILE.exists():
    PASS_FILE.write_text("[admin]=[adminpassword123]\n", encoding="utf-8")

# --------------------------- Safe eval --------------------------- #
import ast
_ALLOWED_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd, ast.Constant,
}
def safe_eval(expr: str) -> float:
    node = ast.parse(expr, mode="eval")
    def _check(n: ast.AST):
        if type(n) not in _ALLOWED_NODES:
            raise ValueError("Unsupported expression")
        for c in ast.iter_child_nodes(n):
            _check(c)
    _check(node)
    return eval(compile(node, "<expr>", "eval"), {"__builtins__": {}}, {})

# --------------------------- Helpers --------------------------- #
def list_dir(path: Path):
    folders, files = [], []
    try:
        for entry in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if entry.is_dir():
                folders.append(entry.name)
            else:
                files.append(entry.name)
    except FileNotFoundError:
        path.mkdir(parents=True, exist_ok=True)
    return folders, files

def within(root: Path, target: Path) -> bool:
    try:
        root = root.resolve()
        target = target.resolve()
        return (target == root) or (root in target.parents)
    except Exception:
        return False

# --------------------------- App Shell --------------------------- #
class MetroOS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Metro OS – PYTHON support ")
        self.title("Don't run with Root/Admin permission, it'll be break you system ")
        self.geometry("1000x620")
        self.minsize(880, 560)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Sidebar
        sidebar = ttk.Frame(self, padding=12)
        sidebar.grid(row=0, column=0, sticky="nsw")
        for i in range(12):
            sidebar.rowconfigure(i, weight=0)
        sidebar.rowconfigure(99, weight=1)

        ttk.Label(sidebar, text="METRO OS", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=(0, 12), sticky="w")

        self.btns = {
            "Home": ttk.Button(sidebar, text="🏠  Home", command=lambda: self.show("Home")),
            "File": ttk.Button(sidebar, text="📁  File Manager", command=lambda: self.show("File")),
            "Clock": ttk.Button(sidebar, text="⏰  Clock", command=lambda: self.show("Clock")),
            "News": ttk.Button(sidebar, text="📰  News", command=lambda: self.show("News")),
            "Calc": ttk.Button(sidebar, text="🧮  Calculator", command=lambda: self.show("Calc")),
            "Sys": ttk.Button(sidebar, text="💻  System Info", command=lambda: self.show("Sys")),
            "DEVMODE": ttk.Button(sidebar, text="🔧  Dev Tools", command=lambda: self.show("DEVMODE")),
            "CD": ttk.Button(sidebar, text="💿  CD/DVD", command=lambda: self.show("CD")),
        }
        r = 1
        for b in self.btns.values():
            b.grid(row=r, column=0, sticky="ew", pady=4)
            r += 1

        ttk.Separator(sidebar).grid(row=r, column=0, sticky="ew", pady=10); r += 1
        ttk.Button(sidebar, text="↻  Restart", command=self.fake_restart).grid(row=r, column=0, sticky="ew", pady=4); r += 1
        ttk.Button(sidebar, text="⏻  Exit", command=self.destroy).grid(row=r, column=0, sticky="ew", pady=4)

        # Main content area
        self.container = ttk.Frame(self, padding=12)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        # create pages (DEVMODE and CD are None -> lazy)
        self.pages: dict[str, BasePage | None] = {
            "Home": HomePage(self.container, self),
            "File": FileManagerPage(self.container, self, root=DATA_DIR),
            "Clock": ClockPage(self.container, self),
            "News": NewsPage(self.container, self, news_dir=NEWS_DIR),
            "Calc": CalculatorPage(self.container, self),
            "Sys": SystemInfoPage(self.container, self),
            "DEVMODE": None,
            "CD": None,
        }

        # grid only created pages (not None)
        for name, page in list(self.pages.items()):
            if page is not None:
                page.grid(row=0, column=0, sticky="nsew")

        # current page is a key string
        self.current_page: str | None = None
        self.show("Home")

        # style
        style = ttk.Style(self)
        try:
            self.call("tk", "scaling", 1.2)
        except Exception:
            pass
        if "vista" in style.theme_names():
            style.theme_use("vista")

    def show(self, name: str):
        # lazy-create DEVMODE/CD as frames inside container (no Toplevel)
        if name not in self.pages:
            return
        if self.pages[name] is None:
            if name == "DEVMODE":
                self.pages[name] = DevModePage(self.container, self, root=DATA_DIR)
            elif name == "CD":
                self.pages[name] = CdromPage(self.container, self, root=CD_DIR)
            # grid the newly created page
            self.pages[name].grid(row=0, column=0, sticky="nsew")

        # call on_hide on previous
        if self.current_page and isinstance(self.pages.get(self.current_page), BasePage):
            prev = self.pages[self.current_page]
            if hasattr(prev, "on_hide"):
                prev.on_hide()

        # raise and set current
        page = self.pages[name]
        page.tkraise()
        self.current_page = name

        # call on_show if present
        if hasattr(page, "on_show"):
            page.on_show()

    def fake_restart(self):
        messagebox.showinfo("Restart", "System restarting...\n(giả lập 1s)")
        self.after(800, lambda: self.show("Home"))

# --------------------------- BasePage --------------------------- #
class BasePage(ttk.Frame):
    def __init__(self, parent, app: MetroOS):
        super().__init__(parent)
        self.app = app

# --------------------------- Pages --------------------------- #
class HomePage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="Welcome to Metro OS – PYTHON support", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        grid = ttk.Frame(self); grid.pack(fill="both", expand=True)
        for i in range(3): grid.columnconfigure(i, weight=1)
        for i in range(2): grid.rowconfigure(i, weight=1)

        def tile(text, cmd):
            f = ttk.Frame(grid, padding=12, relief="ridge")
            ttk.Label(f, text=text, font=("Segoe UI", 12, "bold")).pack(pady=(0,8))
            ttk.Button(f, text="Open", command=cmd).pack()
            return f

        tile("📁 File Manager", lambda: app.show("File")).grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        tile("⏰ Clock", lambda: app.show("Clock")).grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        tile("📰 News", lambda: app.show("News")).grid(row=0, column=2, sticky="nsew", padx=8, pady=8)
        tile("🧮 Calculator", lambda: app.show("Calc")).grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        tile("💻 System Info", lambda: app.show("Sys")).grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        tile("🔧 Dev Tools", lambda: app.show("DEVMODE")).grid(row=1, column=2, sticky="nsew", padx=8, pady=8)


class FileManagerPage(BasePage):
    def __init__(self, parent, app, root: Path):
        super().__init__(parent, app)
        self.root = root.resolve()
        self.current = tk.StringVar(value=str(self.root))

        header = ttk.Frame(self); header.pack(fill="x")
        ttk.Label(header, text="File Manager", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(header, text="Open folder in OS", command=self.open_in_os).pack(side="right")

        nav = ttk.Frame(self); nav.pack(fill="x", pady=(8,6))
        ttk.Label(nav, text="Current:").pack(side="left")
        self.path_entry = ttk.Entry(nav, textvariable=self.current)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(nav, text="Go", command=self.go_to_entry).pack(side="left", padx=2)
        ttk.Button(nav, text="Root", command=self.go_root).pack(side="left", padx=2)
        ttk.Button(nav, text="Back", command=self.go_back).pack(side="left", padx=2)

        body = ttk.PanedWindow(self, orient="horizontal"); body.pack(fill="both", expand=True)
        left = ttk.Frame(body); body.add(left, weight=2)
        right = ttk.Frame(body); body.add(right, weight=3)

        lists = ttk.Frame(left); lists.pack(fill="both", expand=True)
        ttk.Label(lists, text="Folders").grid(row=0, column=0, sticky="w")
        ttk.Label(lists, text="Files").grid(row=0, column=1, sticky="w")
        lists.rowconfigure(1, weight=1); lists.columnconfigure(0, weight=1); lists.columnconfigure(1, weight=1)

        self.lb_dirs = tk.Listbox(lists, activestyle="none"); self.lb_files = tk.Listbox(lists, activestyle="none")
        self.lb_dirs.grid(row=1, column=0, sticky="nsew", padx=(0,6), pady=(4,0)); self.lb_files.grid(row=1, column=1, sticky="nsew", padx=(6,0), pady=(4,0))
        self.lb_dirs.bind("<Double-1>", lambda e: self.open_dir()); self.lb_files.bind("<Double-1>", lambda e: self.view_file())

        actions = ttk.Frame(left); actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Open Folder", command=self.open_dir).pack(side="left")
        ttk.Button(actions, text="View File", command=self.view_file).pack(side="left", padx=6)
        ttk.Button(actions, text="Create File", command=self.create_file).pack(side="left", padx=6)
        ttk.Button(actions, text="Create Folder", command=self.create_folder).pack(side="left", padx=6)
        ttk.Button(actions, text="Delete", command=self.delete_selected).pack(side="left", padx=6)

        ttk.Label(right, text="Preview").pack(anchor="w")
        self.text = tk.Text(right, wrap="word", height=10); self.text.pack(fill="both", expand=True, pady=(4,0))
        self.refresh()

    def on_show(self): self.refresh()

    def open_in_os(self):
        path = Path(self.current.get())
        if os.name == "nt":
            os.startfile(path)
        else:
            os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')

    def go_to_entry(self):
        target = Path(self.current.get()).resolve()
        if within(self.root, target) and target.exists() and target.is_dir():
            self.current.set(str(target)); self.refresh()
        else:
            messagebox.showerror("Blocked", "Can't move to that folder")

    def go_root(self):
        self.current.set(str(self.root)); self.refresh()

    def go_back(self):
        cur = Path(self.current.get()).resolve()
        if cur != self.root:
            self.current.set(str(cur.parent)); self.refresh()

    def refresh(self):
        path = Path(self.current.get()).resolve()
        if not within(self.root, path):
            self.current.set(str(self.root)); path = self.root
        self.lb_dirs.delete(0, "end"); self.lb_files.delete(0, "end")
        dirs, files = list_dir(path)
        for d in dirs: self.lb_dirs.insert("end", d)
        for f in files: self.lb_files.insert("end", f)

    def open_dir(self):
        sel = self.lb_dirs.curselection(); 
        if not sel: return
        name = self.lb_dirs.get(sel[0]); target = (Path(self.current.get()) / name).resolve()
        if target.exists() and target.is_dir() and within(self.root, target):
            self.current.set(str(target)); self.refresh()

    def view_file(self):
        sel = self.lb_files.curselection(); 
        if not sel: return
        name = self.lb_files.get(sel[0]); target = (Path(self.current.get()) / name).resolve()
        try: content = target.read_text(encoding="utf-8", errors="replace")
        except Exception as e: content = f"[ERROR] {e}"
        self.text.delete("1.0", "end"); self.text.insert("1.0", content)

    def create_file(self):
        name = simple_prompt(self, "Create File", "File name:")
        if not name: return
        target = (Path(self.current.get()) / name).resolve()
        if not within(self.root, target): return messagebox.showerror("Blocked", "Invalid path")
        try:
            target.parent.mkdir(parents=True, exist_ok=True); target.write_text("", encoding="utf-8"); self.refresh()
        except Exception as e: messagebox.showerror("Error", str(e))

    def create_folder(self):
        name = simple_prompt(self, "Create Folder", "Folder name:")
        if not name: return
        target = (Path(self.current.get()) / name).resolve()
        if not within(self.root, target): return messagebox.showerror("Blocked", "Invalid path")
        try: target.mkdir(parents=True, exist_ok=True); self.refresh()
        except Exception as e: messagebox.showerror("Error", str(e))

    def delete_selected(self):
        base = Path(self.current.get())
        if self.lb_files.curselection():
            name = self.lb_files.get(self.lb_files.curselection()[0]); target = (base / name).resolve()
        elif self.lb_dirs.curselection():
            name = self.lb_dirs.get(self.lb_dirs.curselection()[0]); target = (base / name).resolve()
        else: return
        if not within(self.root, target): return messagebox.showerror("Blocked", "Can't delete")
        if not messagebox.askyesno("Confirm", f"Delete: {target.name}?"): return
        try:
            if target.is_dir():
                for rootp, dirs, files in os.walk(target, topdown=False):
                    rp = Path(rootp)
                    for f in files: (rp / f).unlink(missing_ok=True)
                    for d in dirs: (rp / d).rmdir()
                target.rmdir()
            else:
                target.unlink(missing_ok=True)
            self.refresh(); self.text.delete("1.0", "end")
        except Exception as e:
            messagebox.showerror("Error", str(e))

class ClockPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="Clock", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        self.lbl = ttk.Label(self, text="", font=("Consolas", 40, "bold")); self.lbl.pack(pady=30)
        self._tick_job = None

    def on_show(self): self._tick()
    def on_hide(self):
        if self._tick_job: self.after_cancel(self._tick_job); self._tick_job = None

    def _tick(self):
        self.lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        self._tick_job = self.after(1000, self._tick)

class NewsPage(BasePage):
    def __init__(self, parent, app, news_dir: Path):
        super().__init__(parent, app)
        self.news_dir = news_dir
        ttk.Label(self, text="News Reader", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        top = ttk.Frame(self); top.pack(fill="x", pady=(8,6))
        ttk.Button(top, text="Reload", command=self.reload).pack(side="left")
        ttk.Button(top, text="Add .txt…", command=self.add_news_file).pack(side="left", padx=6)

        body = ttk.PanedWindow(self, orient="horizontal"); body.pack(fill="both", expand=True)
        left = ttk.Frame(body); right = ttk.Frame(body); body.add(left, weight=1); body.add(right, weight=2)

        ttk.Label(left, text="Files (.txt)").pack(anchor="w")
        self.lb = tk.Listbox(left, activestyle="none"); self.lb.pack(fill="both", expand=True, pady=(4,0))
        self.lb.bind("<Double-1>", lambda e: self.open_selected())

        ttk.Label(right, text="Content").pack(anchor="w")
        self.text = tk.Text(right, wrap="word"); self.text.pack(fill="both", expand=True, pady=(4,0))
        self.reload()

    def reload(self):
        self.lb.delete(0, "end")
        files = sorted([p.name for p in self.news_dir.glob("*.txt")])
        for n in files: self.lb.insert("end", n)

    def open_selected(self):
        if not self.lb.curselection(): return
        name = self.lb.get(self.lb.curselection()[0]); p = self.news_dir / name
        try: content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e: content = f"[ERROR] {e}"
        self.text.delete("1.0", "end"); self.text.insert("1.0", content)

    def add_news_file(self):
        path = filedialog.askopenfilename(title="Choose .txt", filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path: return
        src = Path(path); dst = self.news_dir / src.name
        if dst.exists() and not messagebox.askyesno("Overwrite", f"{dst.name} exists. Replace?"): return
        try: dst.write_text(src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"); self.reload()
        except Exception as e: messagebox.showerror("Error", str(e))

class CalculatorPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="Calculator", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        row = ttk.Frame(self); row.pack(fill="x", pady=(10,6))
        ttk.Label(row, text="Expression:").pack(side="left")
        self.expr = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.expr); entry.pack(side="left", fill="x", expand=True, padx=6)
        entry.bind("<Return>", lambda e: self.calculate())
        ttk.Button(row, text="=", command=self.calculate).pack(side="left")
        self.result = ttk.Label(self, text="Enter an expression, e.g. 3+5*2"); self.result.pack(anchor="w", pady=(4,0))

    def calculate(self):
        expr = self.expr.get().strip()
        if not expr: return
        try:
            val = safe_eval(expr)
            if isinstance(val, (int, float)) and math.isfinite(val):
                self.result.config(text=f"{expr} = {val}")
            else:
                self.result.config(text="Invalid or non-finite result")
        except ZeroDivisionError:
            self.result.config(text="Division by zero!")
        except Exception as e:
            self.result.config(text=f"Invalid input: {e}")

class SystemInfoPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        ttk.Label(self, text="System Information", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        self.box = tk.Text(self, wrap="word", height=18); self.box.pack(fill="both", expand=True, pady=(8,0))
        ttk.Button(self, text="Refresh", command=self.refresh).pack(anchor="e", pady=8); self.refresh()

    def refresh(self):
        info = []
        info.append(f"Computer Name: {socket.gethostname()}")
        info.append(f"Username: {getpass.getuser()}")
        info.append(f"Operating System: {platform.system()} {platform.release()}")
        cpu = platform.processor() or platform.machine(); info.append(f"Processor: {cpu}")
        try:
            import shutil
            total, used, free = shutil.disk_usage(str(BASE))
            info.append(f"Disk Total: {total // (1024**3)} GB")
            info.append(f"Disk Used : {used // (1024**3)} GB")
            info.append(f"Disk Free : {free // (1024**3)} GB")
        except Exception:
            info.append("Disk: (unknown)")
        info.append("RAM Size: (unknown without psutil)")
        self.box.delete("1.0", "end"); self.box.insert("1.0", "\n".join(info))

# --------------------------- Dev & CD pages (frames, lazy) --------------------------- #
class DevModePage(BasePage):
    def __init__(self, parent, app, root: Path):
        super().__init__(parent, app)
        self.root = root
        ttk.Label(self, text="Developer Tools", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        body = ttk.Frame(self); body.pack(fill="both", expand=True, pady=(8,0))
        ttk.Button(body, text="System File Reader", command=self.dev_file_reader).pack(fill="x", pady=4)
        ttk.Button(body, text="Delete the System (gag)", command=self.dev_delete_gag).pack(fill="x", pady=4)
        ttk.Button(body, text="Reset (placeholder)", command=lambda: messagebox.showinfo("Reset", "Reset (placeholder)")).pack(fill="x", pady=4)

        # file reader area
        self.fr_list = tk.Listbox(body); self.fr_text = tk.Text(body, height=12, wrap="word")
        self.fr_list.pack(side="left", fill="both", expand=True, padx=(0,6))
        self.fr_text.pack(side="left", fill="both", expand=True)
        self.fr_list.bind("<<ListboxSelect>>", lambda e: self._open_selected())

        self.reload_files()

    def reload_files(self):
        self.fr_list.delete(0, "end")
        try:
            files = sorted([p for p in BASE.iterdir()])
            for p in files:
                self.fr_list.insert("end", p.name)
        except Exception:
            pass

    def dev_file_reader(self):
        # just refresh the list (already shown in area)
        self.reload_files()
        messagebox.showinfo("File Reader", "Select a file from the list to view its content on the right.")

    def _open_selected(self):
        sel = self.fr_list.curselection()
        if not sel: return
        name = self.fr_list.get(sel[0])
        p = BASE / name
        if not p.is_file():
            self.fr_text.delete("1.0", "end"); self.fr_text.insert("1.0", "(not a regular file)")
            return
        try: content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e: content = f"[ERROR] {e}"
        self.fr_text.delete("1.0", "end"); self.fr_text.insert("1.0", content)

    def dev_delete_gag(self):
        if not messagebox.askyesno("Confirm", "Are you sure? This is just a gag."):
            return
        # show gag output in text area
        self.fr_text.delete("1.0", "end")
        self.fr_text.insert("1.0", "goodbye\n")
        def loop():
            self.fr_text.insert("end", "Error: System file not found!\nNo\n")
            self.after(800, loop)
        loop()

class CdromPage(BasePage):
    def __init__(self, parent, app, root: Path):
        super().__init__(parent, app)
        self.root = root
        ttk.Label(self, text="CD/DVD Reader", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        body = ttk.Frame(self); body.pack(fill="both", expand=True, pady=(8,0))
        left = ttk.Frame(body); left.pack(side="left", fill="both", expand=True, padx=(0,6))
        right = ttk.Frame(body); right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Available CD files:").pack(anchor="w")
        self.lb = tk.Listbox(left); self.lb.pack(fill="both", expand=True); self.lb.bind("<Double-1>", lambda e: self.open_selected())
        ttk.Button(left, text="Refresh", command=self.reload).pack(fill="x", pady=4)

        ttk.Label(right, text="Content").pack(anchor="w")
        self.text = tk.Text(right, wrap="word"); self.text.pack(fill="both", expand=True)

        self.reload()

    def reload(self):
        self.lb.delete(0, "end")
        files = sorted([p.name for p in self.root.glob("*.txt")])
        for n in files: self.lb.insert("end", n)

    def open_selected(self):
        sel = self.lb.curselection()
        if not sel: return
        name = self.lb.get(sel[0]); p = self.root / name
        try: c = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e: c = f"[ERROR] {e}"
        self.text.delete("1.0", "end"); self.text.insert("1.0", c)

# --------------------------- Simple prompt --------------------------- #
def simple_prompt(parent, title, label):
    val = simpledialog.askstring(title, label, parent=parent)
    return val

# --------------------------- Main --------------------------- #
if __name__ == "__main__":
    app = MetroOS()
    app.mainloop()

