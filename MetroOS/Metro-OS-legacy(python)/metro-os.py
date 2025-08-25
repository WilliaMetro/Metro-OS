#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metro OS – Python Console Edition (Arrow-key Menus)
---------------------------------------------------
Chạy trên Linux/macOS/Windows (Windows cần: pip install windows-curses)
Python 3.9+

Tính năng:
- Menu điều hướng bằng phím mũi tên + Enter (curses)
- Vẫn gõ được chữ trong màn hình menu (hiển thị "Typed: ...")
- Các màn hình con (File Manager, Clock, News, Calculator...) giữ nguyên kiểu nhập cũ
"""
from __future__ import annotations

import os
import sys
import time
import math
import random
import platform
import getpass
import socket
import ctypes  # cần cho is_admin() trên Windows
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# ---- Thêm curses cho menu mũi tên ----
import curses

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

# Seed default admin for password manager if missing
if not PASS_FILE.exists():
    PASS_FILE.write_text("[admin]=[adminpassword123]\n", encoding="utf-8")

# --------------------------- Utilities --------------------------- #

def is_admin():
    try:
        if os.name == 'nt':  # Windows
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:  # Linux / macOS / Unix
            return os.geteuid() == 0
    except:
        return False

if is_admin():
    print("\033[91m[WARNING] you mustn't run this code with admin/root permissions!\033[0m")
    print("it's can be break your system.")
    sys.exit(1)
else:
    print("please run with user permissions.")

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg: str = "Press Enter to continue..."):
    try:
        input(msg)
    except EOFError:
        pass

def header(title: str):
    bar = "=" * 53
    print(bar)
    print(title.center(53))
    print(bar)

def list_dir(path: Path) -> Tuple[list[str], list[str]]:
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

# --------------------------- Safe Calculator --------------------------- #
import ast

_ALLOWED_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd,
    ast.Constant,
}

def safe_eval(expr: str) -> float:
    node = ast.parse(expr, mode="eval")
    def _check(n: ast.AST):
        if type(n) not in _ALLOWED_NODES:
            raise ValueError("Unsupported expression")
        for child in ast.iter_child_nodes(n):
            _check(child)
    _check(node)
    return eval(compile(node, "<expr>", "eval"), {"__builtins__": {}}, {})

# --------------------------- Curses Arrow Menu --------------------------- #
def run_arrow_menu(title: str, items: list[str], footer: str = "", typed_hint: bool = True) -> int:
    """
    Hiển thị menu mũi tên. Trả về index đã chọn.
    Dùng curses.wrapper để tự reset terminal sau khi thoát.
    """
    def inner(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(False)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)  # highlight
        curses.init_pair(2, curses.COLOR_YELLOW, -1)               # title/footer

        idx = 0
        typed = ""

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # Title
            if title:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(1, max(0, w//2 - len(title)//2), title)
                stdscr.attroff(curses.color_pair(2))

            # Draw items
            start_y = max(3, h//2 - len(items)//2)
            for i, it in enumerate(items):
                text = f"[ {it} ]" if i == idx else f"  {it}  "
                x = max(0, w//2 - len(text)//2)
                if i == idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(start_y + i, x, text)
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(start_y + i, x, text)

            # Footer
            if footer:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(h-2, 2, footer[:max(0, w-4)])
                stdscr.attroff(curses.color_pair(2))

            # Typed echo
            if typed_hint:
                show = f"Typed: {typed}"
                stdscr.addstr(h-3, 2, show[:max(0, w-4)])

            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP:
                idx = (idx - 1) % len(items)
            elif key == curses.KEY_DOWN:
                idx = (idx + 1) % len(items)
            elif key in (curses.KEY_ENTER, 10, 13):
                return idx
            elif key in (27,):  # ESC
                return -1
            elif 32 <= key <= 126:
                # gõ chữ thường/số sẽ được hiện ra
                typed += chr(key)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                typed = typed[:-1]

    return curses.wrapper(inner)

# --------------------------- Screens --------------------------- #
def boot_menu():
    while True:
        options = ["Sign in", "System setting", "Exit"]
        footer = "↑/↓ to choose • Enter insert • F2: Dev • F3: CDROM • F4: Shop • ESC: escape"
        choice = run_arrow_menu("BOOT MENU", options, footer=footer)

        # F-key không bắt trực tiếp ở đây vì wrapper kết thúc sau khi chọn.
        # Ta map qua các mục chính, còn Dev/CD/Shop sẽ có lối đi trong System menu.
        if choice == 0:
            system_menu()
        elif choice == 1:
            setting_menu()
        elif choice == 2 or choice == -1:
            exit_screen()
            return

def system_menu():
    while True:
        options = [
            "File Manager",
            "Clock",
            "News",
            "Calculator",
            "System information",
            "Password manager",
            "Restart",
            "Shutdown",
            "Back to Boot Menu",
            "Dev Tools",
            "CD/DVD ROM",
            "Shop (placeholder)"
        ]
        footer = "↑/↓ choose • Enter • ESC: back"
        sel = run_arrow_menu("WELCOME TO METRO OS – PYTHON support", options, footer=footer)
        if sel == -1:
            return
        if options[sel] == "File Manager":
            file_manager()
        elif options[sel] == "Clock":
            clock_screen()
        elif options[sel] == "News":
            news_reader()
        elif options[sel] == "Calculator":
            calculator()
        elif options[sel] == "System information":
            system_information()
        elif options[sel] == "Password manager":
            password_manager()
        elif options[sel] == "Restart":
            restart_screen()
        elif options[sel] == "Shutdown":
            exit_screen()
            sys.exit(0)
        elif options[sel] == "Back to Boot Menu":
            return
        elif options[sel] == "Dev Tools":
            dev_tool_gate()
        elif options[sel] == "CD/DVD ROM":
            cdrom_menu()
        elif options[sel] == "Shop (placeholder)":
            shop_top()

# --------------------------- File Manager --------------------------- #
def file_manager():
    current = DATA_DIR
    while True:
        clear()
        header("FILE MANAGER")
        print(f"Current Directory: {current}")
        print("-" * 53)
        folders, files = list_dir(current)
        print("[Folders:]")
        if folders:
            for d in folders:
                print(d)
        else:
            print("(none)")
        print("\n[Files:]")
        if files:
            for f in files:
                print(f)
        else:
            print("(none)")
        print("=" * 53)
        print("Type commands:")
        print("  cd <folder>      - open folder")
        print("  back             - previous folder")
        print("  root             - go to root")
        print("  create f|d <name>- create file/folder")
        print("  delete <name>    - delete file/folder")
        print("  view <file>      - show file content")
        print("  E                - exit to System")
        cmd = input("Enter command: ").strip()
        if not cmd:
            continue
        parts = cmd.split()
        action = parts[0].lower()
        try:
            if action == "e":
                return
            elif action == "root":
                current = DATA_DIR
            elif action == "back":
                if current != DATA_DIR:
                    current = current.parent
            elif action == "cd" and len(parts) >= 2:
                target = (current / " ".join(parts[1:])).resolve()
                if target.is_dir() and (DATA_DIR in target.parents or target == DATA_DIR):
                    if target.exists():
                        current = target
                    else:
                        print("Folder not found!"); pause()
                else:
                    print("Blocked: out of root."); pause()
            elif action == "create" and len(parts) >= 3:
                kind, name = parts[1].lower(), " ".join(parts[2:])
                target = current / name
                if kind == "f":
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("", encoding="utf-8")
                elif kind == "d":
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    print("Use: create f <name> OR create d <name>"); pause()
            elif action == "delete" and len(parts) >= 2:
                name = " ".join(parts[1:])
                target = current / name
                if target.is_dir():
                    for root, dirs, files2 in os.walk(target, topdown=False):
                        for f in files2:
                            (Path(root) / f).unlink(missing_ok=True)
                        for d in dirs:
                            (Path(root) / d).rmdir()
                    target.rmdir()
                    print(f"Deleted folder '{name}'")
                    pause()
                elif target.is_file():
                    target.unlink(missing_ok=True)
                    print(f"Deleted file '{name}'")
                    pause()
                else:
                    print("Not found!"); pause()
            elif action == "view" and len(parts) >= 2:
                name = " ".join(parts[1:])
                target = current / name
                if target.is_file():
                    clear(); header("FILE CONTENT")
                    try:
                        print(target.read_text(encoding="utf-8", errors="replace"))
                    except Exception as e:
                        print(f"ERROR: {e}")
                    print("\n" + "=" * 53)
                    pause()
                else:
                    print("File not found!"); pause()
            else:
                print("Unknown command"); pause()
        except Exception as e:
            print(f"Error: {e}"); pause()

# --------------------------- News --------------------------- #
def news_reader():
    while True:
        clear(); header("NEWS READER")
        files = sorted([p.name for p in NEWS_DIR.glob("*.txt")])
        if files:
            print("Available News Files:")
            for i, name in enumerate(files, 1):
                print(f"{i}. {name}")
        else:
            print("No news available.")
        print("\nType number to open, 'r' to refresh, or 'E' to exit.")
        ans = input("Choice: ").strip().lower()
        if ans in ("e", "exit", "q"):
            return
        if ans == "r":
            continue
        if ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(files):
                clear(); header("NEWS")
                p = NEWS_DIR / files[idx]
                print(p.read_text(encoding="utf-8", errors="replace"))
                print("\n" + "=" * 53)
                pause()

# --------------------------- Calculator --------------------------- #
def calculator():
    while True:
        clear(); header("CALCULATOR")
        print("Enter expression (e.g., 3+3, 5*8, 10/2)")
        print("Type 'b' to go back.")
        expr = input("Enter calculation: ").strip()
        if expr.lower() in ("b", "back", "exit", "e"):
            return
        try:
            result = safe_eval(expr)
            if isinstance(result, (int, float)) and (math.isfinite(result)):
                print(f"{expr} = {result}")
            else:
                print("Invalid or non-finite result")
        except ZeroDivisionError:
            scary_error()
        except Exception as e:
            print(f"Invalid input: {e}")
        pause()

def scary_error():
    clear()
    header("!!! ERROR !!!")
    print("SYSTEM INSTABILITY DETECTED! CODE: 0xDEAD0000")
    print("FATAL EXCEPTION IN PROCESSOR CORE\n")
    print("Press Enter to recover...")
    try:
        while True:
            print(f"ERROR DETECTED! SYSTEM FAILURE! WARNING!!! {random.randint(0, 65535)}")
            time.sleep(0.02)
            if sys.stdin in select_readable(timeout=0):
                _ = input()
                break
    except KeyboardInterrupt:
        pass

def select_readable(timeout: float = 0.0):
    try:
        import select
        r, _, _ = select.select([sys.stdin], [], [], timeout)
        return r
    except Exception:
        return []

# --------------------------- Clock --------------------------- #
def clock_screen():
    options = [
        "Exit",
        "Refresh the clock (auto refresh every second)",
        "Refresh once"
    ]

    def draw_menu(stdscr, selected):
        stdscr.clear()
        stdscr.addstr(0, 0, "CLOCK – tic tac tic tac\n\n")
        now = datetime.now().strftime("%H:%M:%S")
        stdscr.addstr(1, 0, now.center(50) + "\n\n")
        
        for idx, option in enumerate(options):
            if idx == selected:
                # highlight option
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 4, 4, option)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 4, 4, option)
        stdscr.refresh()
    
    def main(stdscr):
        curses.curs_set(0)  # hide cursor
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # highlight color

        current_selection = 0

        while True:
            draw_menu(stdscr, current_selection)
            key = stdscr.getch()

            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(options) - 1:
                current_selection += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                # xử lý lựa chọn
                if current_selection == 0:
                    return
                elif current_selection == 1:
                    try:
                        while True:
                            stdscr.clear()
                            stdscr.addstr(0, 0, "CLOCK – tic tac tic tac\n\n")
                            stdscr.addstr(1, 0, datetime.now().strftime("%H:%M:%S").center(50) + "\n\n")
                            stdscr.addstr(3, 0, "Press Ctrl+C to stop auto-refresh")
                            stdscr.refresh()
                            time.sleep(1)
                    except KeyboardInterrupt:
                        pass
                elif current_selection == 2:
                    stdscr.clear()
                    stdscr.addstr(0, 0, "CLOCK – tic tac tic tac\n\n")
                    stdscr.addstr(1, 0, datetime.now().strftime("%H:%M:%S").center(50) + "\n\n")
                    stdscr.addstr(3, 0, "Press any key to return to menu")
                    stdscr.refresh()
                    stdscr.getch()

    curses.wrapper(main)    

# --------------------------- Password Manager --------------------------- #
def password_manager():
    while True:
        options = [
            "Add New User Password",
            "View All User Passwords",
            "Delete user",
            "Back to System Menu"
        ]
        sel = run_arrow_menu("PASSWORD MANAGER", options, footer="↑/↓ chọn • Enter xác nhận • ESC: về trước")
        if sel == -1 or options[sel] == "Back to System Menu":
            return
        if options[sel] == "Add New User Password":
            add_password()
        elif options[sel] == "View All User Passwords":
            view_passwords()
        elif options[sel] == "Delete user":
            delete_user()

def sanitize(s: str) -> str:
    return s.replace("&", "_amp_")

def add_password():
    clear(); header("ADD NEW USER PASSWORD")
    username = input("Enter new username: ").strip()
    password = input("Enter new password: ").strip()
    username, password = sanitize(username), sanitize(password)
    lines = PASS_FILE.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.startswith(f"[{username}]="):
            print(f"Error: User {username} already exists!")
            pause(); return
    with PASS_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{username}]=[{password}]\n")
    print(f"New user {username} added successfully!")
    pause()

def view_passwords():
    clear(); header("VIEW SAVED PASSWORDS")
    dev = getpass.getpass("Enter DEV password to view passwords: ")
    if dev != DEV_PASSWORD:
        print("Incorrect DEV password!"); pause(); return
    if not PASS_FILE.exists():
        ans = input("Password file missing. Create default? (y/n): ").strip().lower()
        if ans == "y":
            PASS_FILE.write_text("[admin]=[adminpassword123]\n", encoding="utf-8")
            print("Created default password file.")
        else:
            print("Canceled.")
    else:
        print(PASS_FILE.read_text(encoding="utf-8", errors="replace"))
    pause()

def delete_user():
    clear(); header("DELETE USER FROM PASSWORD FILE")
    dev = getpass.getpass("Enter DEV password to delete user: ")
    if dev != DEV_PASSWORD:
        print("Incorrect DEV password!"); pause(); return
    username = sanitize(input("Enter the username to delete: ").strip())
    if not PASS_FILE.exists():
        print("No password file."); pause(); return
    lines = PASS_FILE.read_text(encoding="utf-8").splitlines()
    kept = [ln for ln in lines if not ln.startswith(f"[{username}]=")]
    if len(kept) == len(lines):
        print(f"User '{username}' not found!")
    else:
        PASS_FILE.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        print(f"User '{username}' deleted successfully!")
    pause()

# --------------------------- System Information --------------------------- #
def system_information():
    clear(); header("SYSTEM INFORMATION")
    print(f"Computer Name: {socket.gethostname()}")
    print(f"Username: {getpass.getuser()}")
    print(f"Operating System: {platform.system()} {platform.release()}")
    cpu = platform.processor() or platform.machine()
    print(f"Processor: {cpu}")
    try:
        import shutil
        total, used, free = shutil.disk_usage(str(BASE))
        print(f"Available Disk Space: {free // (1024**3)} GB")
    except Exception:
        print("Available Disk Space: (unknown)")
    print("RAM Size: (unknown without psutil)")
    print("=" * 53)
    pause()

# --------------------------- Settings --------------------------- #
def setting_menu():
    while True:
        options = ["RAM setting", "Disk setting", "Back"]
        sel = run_arrow_menu("SYSTEM SETTINGS", options, footer="↑/↓ chọn • Enter xác nhận • ESC: về trước")
        if sel == -1 or options[sel] == "Back":
            return
        if options[sel] == "RAM setting":
            ram_setting()
        elif options[sel] == "Disk setting":
            disk_setting()

def ram_setting():
    clear(); header("RAM SETTING")
    print("you can change 8,388,608 bit a time")
    print("\nMemory 512MB")
    print("Boot by DOS")
    print("Error not found")
    pause()

def disk_setting():
    clear(); header("DISK SETTING")
    print("you can change 12,092,211 bit a time\n")
    print("disk size: 10GB")
    print("free space: 9.4GB")
    print("I'm Disk, I wanna tell you, don't change anything")
    print("because that's your memories\nbye")
    pause()

# --------------------------- Dev Tools --------------------------- #
def dev_tool_gate():
    clear(); header("DEV SAFE SCREEN")
    dev = getpass.getpass("Enter DEV password: ")
    if dev == DEV_PASSWORD:
        print("Access granted!"); time.sleep(0.6)
        dev_mode()
    else:
        print("Incorrect password!"); pause()

def dev_mode():
    while True:
        options = [
            "system file reader (script root)",
            "Delete the system (gag)",
            "reset the system",
            "exit"
        ]
        sel = run_arrow_menu("WELCOME TO DEV TOOL", options, footer="↑/↓ chọn • Enter • ESC: về trước")
        if sel == -1 or options[sel] == "exit":
            return
        if options[sel] == "system file reader (script root)":
            dev_file_reader()
        elif options[sel] == "Delete the system (gag)":
            dev_delete_gag()
        elif options[sel] == "reset the system":
            restart_screen()

def dev_file_reader():
    while True:
        clear(); header("FILE READER (DEV – script root)")
        files = sorted([p.name for p in BASE.iterdir()])
        for i, name in enumerate(files, 1):
            print(f"{i}. {name}")
        print("\nType number to open, 'b' to go back.")
        ans = input("Choice: ").strip().lower()
        if ans in ("b", "back", "e", "exit"):
            return
        if ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(files):
                p = BASE / files[idx]
                clear(); header("FILE CONTENT")
                if p.is_file():
                    try:
                        print(p.read_text(encoding="utf-8", errors="replace"))
                    except Exception as e:
                        print(f"ERROR: {e}")
                else:
                    print("(not a regular file)")
                print("\n" + "=" * 53)
                pause()

def dev_delete_gag():
    clear(); header("ARE YOU SURE")
    ans = input("enter your choice (Y/N): ").strip().upper()
    if ans != "Y":
        print("thank you for choosing"); pause(); return
    clear(); print("goodbye"); time.sleep(1)
    while True:
        print("Error: System file not found!")
        time.sleep(0.5)
        print("No")
        time.sleep(0.5)
        # loop forever until Ctrl+C

# --------------------------- CD/DVD ROM --------------------------- #
def cdrom_menu():
    while True:
        options = ["open CD ROM", "delete CD ROM (placeholder)", "exit"]
        sel = run_arrow_menu("WELCOME TO CD/DVD ROM", options, footer="↑/↓ chọn • Enter • ESC: về trước")
        if sel == -1 or options[sel] == "exit":
            return
        if options[sel] == "open CD ROM":
            open_cd()
        elif options[sel] == "delete CD ROM (placeholder)":
            clear(); header("DELETE CD ROM")
            print("This option can delete files or perform other actions.")
            pause()

def open_cd():
    while True:
        clear(); header("CD READER")
        files = sorted([p.name for p in CD_DIR.glob("*.txt")])
        if files:
            print("Available CD files:")
            for i, name in enumerate(files, 1):
                print(f"{i}. {name}")
        else:
            print("No CD Available")
        print("\nType number to open, 'b' to go back.")
        ans = input("Choice: ").strip().lower()
        if ans in ("b", "back", "e", "exit"):
            return
        if ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(files):
                clear(); header("CD CONTENT")
                p = CD_DIR / files[idx]
                print(p.read_text(encoding="utf-8", errors="replace"))
                print("\n" + "=" * 53)
                pause()

# --------------------------- Misc Screens --------------------------- #
def restart_screen():
    clear(); header("SYSTEM RESTARTING")
    print("The system will restart in 5 seconds...")
    time.sleep(5)

def exit_screen():
    clear(); header("EXIT THE SYSTEM")
    print("see you soon\nsupport by Python")
    pause()

def shop_top():
    clear(); header("SHOP (placeholder)")
    print("Coming soon…")
    pause()

# --------------------------- Main --------------------------- #
if __name__ == "__main__":
    try:
        boot_menu()
    except KeyboardInterrupt:
        print("\nBye!")
