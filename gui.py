#!/usr/bin/env python3
"""MyRPN Calculator — GUI interface using tkinter."""

import sys
import os
import tkinter as tk
from tkinter import font as tkfont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stack import Stack, StackUnderflowError
from parser import parse
from operations import dispatch, RPNError, register, list_operations
from rpn_types import RPNObject, RPNProgram, RPNNumber
from display import format_value
from state import save_state, load_state
from ops.program import execute
import ops  # noqa: F401

# ── Reuse Settings / display-mode ops from main (import triggers @register) ──
from repl import Settings, get_angle_mode


# ══════════════════════════════════════════════════════════════════════════════
#  Colour palette — dark theme resembling the HP 50g body
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg":          "#1a1a2e",   # dark navy body
    "screen_bg":   "#c8d8c0",   # greenish LCD
    "screen_fg":   "#1a1a1a",
    "header_fg":   "#444444",
    "btn_num":     "#e0e0e0",   # white numeric keys
    "btn_num_fg":  "#000000",
    "btn_op":      "#f5a623",   # orange operator keys
    "btn_op_fg":   "#ffffff",
    "btn_fn":      "#3a3a5c",   # dark function keys
    "btn_fn_fg":   "#ffffff",
    "btn_enter":   "#4a90d9",   # blue ENTER
    "btn_enter_fg":"#ffffff",
    "btn_red":     "#d94040",   # red/clear keys
    "btn_red_fg":  "#ffffff",
    "btn_green":   "#2d8659",   # green special
    "btn_green_fg":"#ffffff",
    "entry_bg":    "#ffffff",
    "entry_fg":    "#000000",
    "status_bg":   "#0f0f1e",
    "status_fg":   "#88aacc",
}


class HP50gGUI:
    """Tkinter GUI for the MyRPN simulator."""

    def __init__(self, root):
        self.root = root
        self.root.title("MyRPN Calculator")
        self.root.configure(bg=C["bg"])
        self.root.resizable(False, False)

        # Engine state
        self.stack = Stack()
        self.variables = {}
        self.settings = Settings()
        self._undo_stack = []
        self._history = []
        self._history_idx = -1

        self._load()

        # Fonts
        self.lcd_font = tkfont.Font(family="Consolas", size=16)
        self.lcd_small = tkfont.Font(family="Consolas", size=10)
        self.btn_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self.btn_small = tkfont.Font(family="Segoe UI", size=9)
        self.entry_font = tkfont.Font(family="Consolas", size=14)

        self._build_ui()
        self._refresh_display()

        # Bindings
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── State persistence ────────────────────────────────────────────────
    def _load(self):
        stack_items, saved_vars, saved_settings = load_state()
        for item in stack_items:
            self.stack.push(item)
        self.variables.update(saved_vars)
        if saved_settings:
            self.settings.from_dict(saved_settings)
            if self.settings.angle_mode != "RAD":
                try:
                    import ops.scientific as sci
                    sci._angle_mode = self.settings.angle_mode
                except Exception:
                    pass

    def _save(self):
        self.settings.angle_mode = get_angle_mode()
        save_state(self.stack, self.variables, self.settings.to_dict())

    def _on_close(self):
        self._save()
        self.root.destroy()

    # ── Build UI ─────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = 6

        # ── Screen (LCD) ─────────────────────────────────────────────
        screen_frame = tk.Frame(self.root, bg=C["screen_bg"], bd=3, relief="sunken")
        screen_frame.pack(padx=10, pady=(10, 4), fill="x")

        self.header_label = tk.Label(
            screen_frame, text="", anchor="w", bg=C["screen_bg"],
            fg=C["header_fg"], font=self.lcd_small, padx=6, pady=2
        )
        self.header_label.pack(fill="x")

        self.stack_labels = []
        for lvl in range(4, 0, -1):
            frm = tk.Frame(screen_frame, bg=C["screen_bg"])
            frm.pack(fill="x", padx=4)
            lbl_n = tk.Label(frm, text=f"{lvl}:", width=3, anchor="e",
                             bg=C["screen_bg"], fg=C["header_fg"], font=self.lcd_small)
            lbl_n.pack(side="left")
            lbl_v = tk.Label(frm, text="", anchor="e",
                             bg=C["screen_bg"], fg=C["screen_fg"], font=self.lcd_font)
            lbl_v.pack(side="right", fill="x", expand=True)
            self.stack_labels.append((lvl, lbl_v))

        # ── Input entry ──────────────────────────────────────────────
        entry_frame = tk.Frame(self.root, bg=C["bg"])
        entry_frame.pack(padx=10, pady=4, fill="x")

        self.entry = tk.Entry(
            entry_frame, font=self.entry_font,
            bg=C["entry_bg"], fg=C["entry_fg"],
            insertbackground=C["entry_fg"], relief="sunken", bd=2
        )
        self.entry.pack(fill="x", ipady=4)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<KP_Enter>", self._on_enter)
        self.entry.bind("<Up>", self._on_history_up)
        self.entry.bind("<Down>", self._on_history_down)
        self.entry.bind("<Escape>", lambda e: self._clear_entry())
        self.entry.focus_set()

        # ── Error / status bar ───────────────────────────────────────
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var, anchor="w",
            bg=C["status_bg"], fg=C["status_fg"], font=self.lcd_small,
            padx=8, pady=2
        )
        self.status_label.pack(fill="x", padx=10)

        # ── Button grid ──────────────────────────────────────────────
        btn_frame = tk.Frame(self.root, bg=C["bg"])
        btn_frame.pack(padx=10, pady=(4, 10))

        # Button definitions: (text, command_or_input, color_key, col_span)
        rows = [
            # Row 0 — trig / scientific
            [("SIN",   "SIN",   "fn", 1), ("COS",   "COS",   "fn", 1),
             ("TAN",   "TAN",   "fn", 1), ("√",     "SQRT",  "fn", 1),
             ("x²",    "SQ",    "fn", 1), ("yˣ",    "^",     "fn", 1)],
            # Row 1 — more functions
            [("LOG",   "LOG",   "fn", 1), ("LN",    "LN",    "fn", 1),
             ("EXP",   "EXP",   "fn", 1), ("1/x",   "INV",   "fn", 1),
             ("+/−",   "NEG",   "fn", 1), ("π",     "PI",    "fn", 1)],
            # Row 2 — stack operations
            [("SWAP",  "SWAP",  "green", 1), ("DUP",  "DUP",  "green", 1),
             ("OVER",  "OVER",  "green", 1), ("ROT",  "ROT",  "green", 1),
             ("UNDO",  "_UNDO", "green", 1), ("DROP", "DROP",  "red", 1)],
            # Row 3 — STO/RCL + mode
            [("STO",   "_STO",  "fn", 1), ("RCL",   "_RCL",  "fn", 1),
             ("VARS",  "VARS",  "fn", 1), ("DEG",  "_ANGLETOGGLE", "fn", 1),
             ("«»",    "_PROG", "fn", 1), ("CLR",   "CLEAR", "red", 1)],
            # Row 4 — numbers 7-9, /
            [("7", "_7", "num", 1), ("8", "_8", "num", 1),
             ("9", "_9", "num", 1), ("÷",  "/",  "op", 1),
             ("(",  "_(", "fn", 1), ("EEX", "_EEX", "fn", 1)],
            # Row 5 — numbers 4-6, *
            [("4", "_4", "num", 1), ("5", "_5", "num", 1),
             ("6", "_6", "num", 1), ("×",  "*",  "op", 1),
             ("{}", "_LIST", "fn", 1), ("MOD", "MOD", "fn", 1)],
            # Row 6 — numbers 1-3, -
            [("1", "_1", "num", 1), ("2", "_2", "num", 1),
             ("3", "_3", "num", 1), ("−",  "-",  "op", 1),
             ("ABS", "ABS", "fn", 1), ("!",  "!",  "fn", 1)],
            # Row 7 — 0, ., +, ENTER
            [("0", "_0", "num", 1), (".", "_.", "num", 1),
             ("⌫", "_BS", "red", 1), ("+",  "+",  "op", 1),
             ("ENTER", "_ENTER", "enter", 2)],
        ]

        for r, row in enumerate(rows):
            col = 0
            for (text, cmd, color, span) in row:
                bg = C[f"btn_{color}"]
                fg = C[f"btn_{color}_fg"]
                b = tk.Button(
                    btn_frame, text=text, width=5 * span, height=1,
                    bg=bg, fg=fg, activebackground=bg,
                    activeforeground=fg, font=self.btn_font, bd=1,
                    relief="raised",
                    command=lambda c=cmd: self._on_button(c)
                )
                b.grid(row=r, column=col, columnspan=span,
                       padx=2, pady=2, sticky="nsew")
                col += span

        # Make columns equal width
        for c in range(6):
            btn_frame.columnconfigure(c, weight=1, minsize=62)

    # ── Display refresh ──────────────────────────────────────────────
    def _refresh_display(self):
        angle = get_angle_mode()
        nf = self.settings.num_format
        fd = self.settings.fix_digits
        parts = [angle]
        parts.append(f"{nf} {fd}" if nf != "STD" and fd is not None else nf)
        self.header_label.config(text="  ".join(parts))

        data = self.stack.to_list()
        for (lvl, lbl) in self.stack_labels:
            idx = len(data) - lvl
            if idx >= 0:
                lbl.config(text=format_value(data[idx], nf, fd))
            else:
                lbl.config(text="")

    def _set_status(self, msg, is_error=False):
        self.status_var.set(msg)
        self.status_label.config(fg="#ff6666" if is_error else C["status_fg"])
        if msg:
            self.root.after(4000, lambda: self.status_var.set("")
                           if self.status_var.get() == msg else None)

    def _clear_entry(self):
        self.entry.delete(0, tk.END)

    # ── Core execution ───────────────────────────────────────────────
    def _executor(self, prog_tokens, stk, vrs):
        execute(prog_tokens, stk, vrs)

    def _execute_line(self, line):
        """Execute an input line against the RPN engine."""
        line = line.strip()
        if not line:
            return

        # Save to history
        if not self._history or self._history[-1] != line:
            self._history.append(line)
        self._history_idx = -1

        # Snapshot for UNDO
        self._undo_stack.append(self.stack.snapshot())
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

        try:
            tokens = parse(line)
            for token in tokens:
                dispatch(token, self.stack, self.variables, self._executor)
            self.settings.angle_mode = get_angle_mode()
            self._set_status("")
        except (RPNError, StackUnderflowError) as e:
            self._set_status(f"Error: {e}", is_error=True)
        except Exception as e:
            self._set_status(f"Error: {e}", is_error=True)

        self._refresh_display()

    def _do_undo(self):
        if self._undo_stack:
            self.stack.restore(self._undo_stack.pop())
            self._set_status("UNDO")
            self._refresh_display()
        else:
            self._set_status("Nothing to undo", is_error=True)

    # ── Event handlers ───────────────────────────────────────────────
    def _on_enter(self, event=None):
        line = self.entry.get().strip()
        if line:
            self._execute_line(line)
        else:
            # Empty ENTER = DUP (like the HP 50g)
            if self.stack.depth() > 0:
                self._execute_line("DUP")
        self._clear_entry()

    def _on_history_up(self, event):
        if not self._history:
            return
        if self._history_idx == -1:
            self._history_idx = len(self._history) - 1
        elif self._history_idx > 0:
            self._history_idx -= 1
        self._clear_entry()
        self.entry.insert(0, self._history[self._history_idx])

    def _on_history_down(self, event):
        if not self._history or self._history_idx == -1:
            return
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self._clear_entry()
            self.entry.insert(0, self._history[self._history_idx])
        else:
            self._history_idx = -1
            self._clear_entry()

    def _on_button(self, cmd):
        """Handle button press."""
        # Digit / decimal point input — append to entry
        if cmd.startswith("_") and len(cmd) == 2 and cmd[1] in "0123456789.":
            self.entry.insert(tk.END, cmd[1])
            self.entry.focus_set()
            return

        # Backspace
        if cmd == "_BS":
            content = self.entry.get()
            if content:
                self.entry.delete(len(content) - 1, tk.END)
            else:
                # If entry empty, DROP
                self._execute_line("DROP")
            self.entry.focus_set()
            return

        # ENTER
        if cmd == "_ENTER":
            self._on_enter()
            self.entry.focus_set()
            return

        # UNDO
        if cmd == "_UNDO":
            self._do_undo()
            self.entry.focus_set()
            return

        # STO — prompt-like: if entry has text, use it as value + ask for name
        if cmd == "_STO":
            content = self.entry.get().strip()
            if content:
                # If entry has a name like 'X', push current entry value then STO
                self._execute_line(content)
                self._clear_entry()
            self._set_status("Type variable name (e.g. 'X') then press ENTER to STO")
            self.entry.insert(0, "'" )
            self.entry.focus_set()
            # Next ENTER will push 'NAME', user should type: 'X' STO
            return

        # RCL
        if cmd == "_RCL":
            self._set_status("Type variable name (e.g. 'X') then press ENTER to RCL")
            self.entry.insert(0, "'")
            self.entry.focus_set()
            return

        # Program delimiters 
        if cmd == "_PROG":
            self.entry.insert(tk.END, "<< ")
            self.entry.focus_set()
            return

        # List delimiters
        if cmd == "_LIST":
            self.entry.insert(tk.END, "{ ")
            self.entry.focus_set()
            return

        # Open paren (for grouping in entry)
        if cmd == "_(":
            self.entry.insert(tk.END, "(")
            self.entry.focus_set()
            return

        # EEX (scientific notation entry)
        if cmd == "_EEX":
            self.entry.insert(tk.END, "e")
            self.entry.focus_set()
            return

        # Angle mode toggle
        if cmd == "_ANGLETOGGLE":
            current = get_angle_mode()
            next_mode = {"RAD": "DEG", "DEG": "GRAD", "GRAD": "RAD"}[current]
            self._execute_line(next_mode)
            self.entry.focus_set()
            return

        # If there's text in the entry, push it first, then execute the op
        content = self.entry.get().strip()
        if content:
            self._execute_line(content)
            self._clear_entry()

        # Execute the command
        self._execute_line(cmd)
        self.entry.focus_set()


def main():
    root = tk.Tk()
    HP50gGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
