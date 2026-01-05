import os
import json
import wave
import struct
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, scrolledtext

# =========================
# Theme
# =========================

BG = "#14FFDC"
FG = "hotpink"

BTN_BG = "#14FFDC"
BTN_FG = "hotpink"

ENTRY_BG = "hotpink"
ENTRY_FG = "#14FFDC"

LOG_BG = "hotpink"
LOG_FG = "#14FFDC"

# =========================
# Defaults & Config Helpers
# =========================

DEFAULTS = {
    "text": "Merry Christmas",
    "pos": 1224,
    "encoding": "ascii",
    "cue_id": 1,
    "recursive": False,
    "output_mode": "inplace",  # inplace | newfile
    "suffix": "_labeled",
}

def load_config_json(path):
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Config JSON must be an object")
    return data

def merge_config(gui_vals, json_vals, cli_vals):
    cfg = dict(DEFAULTS)
    cfg.update(gui_vals or {})
    cfg.update(json_vals or {})
    cfg.update({k: v for k, v in (cli_vals or {}).items() if v is not None})
    return cfg

# =========================
# WAV cue writer
# =========================

def _pad_even(b: bytes) -> bytes:
    return b if len(b) % 2 == 0 else b + b"\x00"

def add_label_to_wav(path, cfg):
    with wave.open(path, "rb") as w:
        params = w.getparams()
        frames = w.readframes(params.nframes)

    cue_id = int(cfg["cue_id"])
    pos = int(cfg["pos"])

    cue_point = struct.pack("<II4sIII", cue_id, pos, b"data", 0, 0, pos)
    cue_payload = _pad_even(struct.pack("<I", 1) + cue_point)

    text_bytes = str(cfg["text"]).encode(cfg["encoding"])
    labl_payload = _pad_even(struct.pack("<I", cue_id) + text_bytes + b"\x00")
    labl_chunk = _pad_even(b"labl" + struct.pack("<I", len(labl_payload)) + labl_payload)
    list_payload = _pad_even(b"adtl" + labl_chunk)

    if cfg.get("output_mode") == "newfile":
        base, ext = os.path.splitext(path)
        out_path = base + cfg.get("suffix", "_labeled") + ext
    else:
        out_path = path

    tmp = out_path + ".tmp"

    with wave.open(tmp, "wb") as w:
        w.setparams(params)
        w.writeframes(frames)

    with open(tmp, "ab") as f:
        f.write(b"cue ")
        f.write(struct.pack("<I", len(cue_payload)))
        f.write(cue_payload)

        f.write(b"LIST")
        f.write(struct.pack("<I", len(list_payload)))
        f.write(list_payload)

    size = os.path.getsize(tmp)
    with open(tmp, "r+b") as f:
        f.seek(4)
        f.write(struct.pack("<I", size - 8))

    os.replace(tmp, out_path)

# =========================
# GUI
# =========================

class App:
    def __init__(self, root):
        self.root = root
        root.title("༶･･ᗰદ૨૨ʏ ᘓમ₂ıડτન੨ड･･༶ Label Creator ✩*⋆ ⍋*☪⋆⍋⋆*✩ᒃ♪♬")

        # ---- Global mono font (use log-like monospace everywhere) ----
        mono_candidates = [
            "SF Mono", "Menlo", "Monaco",
            "Consolas", "Cascadia Mono", "Courier New",
            "DejaVu Sans Mono", "Liberation Mono",
        ]
        available = set(tkfont.families(root))
        mono_family = next((f for f in mono_candidates if f in available), None)

        base = tkfont.nametofont("TkDefaultFont")
        if mono_family:
            base.configure(family=mono_family, size=13)
        else:
            base.configure(size=13)

        for name in [
            "TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont",
            "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont",
            "TkIconFont", "TkTooltipFont"
        ]:
            try:
                tkfont.nametofont(name).configure(**base.actual())
            except Exception:
                pass

        root.configure(bg=BG)

        self.folder = tk.StringVar()
        self.config = tk.StringVar()
        self.text = tk.StringVar(value=DEFAULTS["text"])
        self.pos = tk.StringVar(value=str(DEFAULTS["pos"]))

        # NEW: output_mode option (dropdown)
        self.output_mode = tk.StringVar(value=DEFAULTS["output_mode"])

        frm = tk.Frame(root, padx=10, pady=10, bg=BG)
        frm.pack(fill="both", expand=True)

        def style_label(lbl: tk.Label):
            lbl.configure(bg=BG, fg=FG)

        def style_entry(ent: tk.Entry):
            ent.configure(bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)

        def style_button(btn: tk.Button):
            btn.configure(
                bg=BTN_BG,
                fg=BTN_FG,
                activebackground=BTN_BG,
                activeforeground=BTN_FG,
                relief="flat",
                bd=0,
                highlightthickness=0,
                highlightbackground=BTN_BG,
                padx=12,
                pady=6,
                cursor="hand2",
            )

        def style_optionmenu(om: tk.OptionMenu):
            om.configure(
                bg=BTN_BG,
                fg=BTN_FG,
                activebackground=BTN_BG,
                activeforeground=BTN_FG,
                highlightthickness=0,
                bd=0,
                relief="flat",
                cursor="hand2",
            )
            m = om["menu"]
            m.configure(
                bg=BTN_BG,
                fg=BTN_FG,
                activebackground=BTN_BG,
                activeforeground=BTN_FG,
                bd=0,
                relief="flat",
            )

        def row(r, label, var, btn=None):
            lbl = tk.Label(frm, text=label)
            style_label(lbl)
            lbl.grid(row=r, column=0, sticky="w")

            ent = tk.Entry(frm, textvariable=var, width=28)
            style_entry(ent)
            ent.grid(row=r, column=1, sticky="we", padx=5)

            if btn:
                b = tk.Button(frm, text="Choose…", command=btn)
                style_button(b)
                b.grid(row=r, column=2, sticky="e")

        row(0, "Folder", self.folder, self.choose_folder)
        row(1, "Config (JSON)", self.config, self.choose_config)
        row(2, "Label text", self.text)
        row(3, "Position", self.pos)

        lbl_mode = tk.Label(frm, text="Output mode")
        style_label(lbl_mode)
        lbl_mode.grid(row=4, column=0, sticky="w")

        om = tk.OptionMenu(frm, self.output_mode, "inplace", "newfile")
        style_optionmenu(om)
        om.grid(row=4, column=1, sticky="w", padx=5)

        btns = tk.Frame(frm, bg=BG)
        btns.grid(row=5, column=0, columnspan=3, sticky="w", pady=10)

        run_btn = tk.Button(btns, text="Run", command=self.run)
        clr_btn = tk.Button(btns, text="Clear", command=self.clear_log)
        style_button(run_btn)
        style_button(clr_btn)
        run_btn.pack(side="left")
        clr_btn.pack(side="left", padx=8)

        self.log = scrolledtext.ScrolledText(
            frm,
            height=14,
            bg=LOG_BG,
            fg=LOG_FG,
            insertbackground=LOG_FG,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BTN_BG,
            highlightcolor=BTN_BG,
        )
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew")
        self.log.configure(state="disabled")

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(6, weight=1)

    def _log_write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def logln(self, s):
        self._log_write(s + "\n")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def choose_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.folder.set(p)

    def choose_config(self):
        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not p:
            return
        self.config.set(p)
        try:
            cfg = load_config_json(p)
            if "text" in cfg:
                self.text.set(str(cfg["text"]))
            if "pos" in cfg:
                self.pos.set(str(cfg["pos"]))
            # If JSON contains output_mode, reflect it in the dropdown
            if "output_mode" in cfg and str(cfg["output_mode"]) in ("inplace", "newfile"):
                self.output_mode.set(str(cfg["output_mode"]))
        except Exception as e:
            messagebox.showerror("Config error", str(e))

    def run(self):
        folder = self.folder.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Invalid folder")
            return

        try:
            gui_vals = {
                "text": self.text.get(),
                "pos": int(self.pos.get()),
                "output_mode": self.output_mode.get(),  # NEW
            }
        except ValueError:
            messagebox.showerror("Error", "Position must be an integer")
            return

        json_vals = load_config_json(self.config.get()) if self.config.get() else {}
        cfg = merge_config(gui_vals, json_vals, {})

        wavs = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(".wav")
        )
        if not wavs:
            messagebox.showinfo("No files", "No .wav files found in the selected folder.")
            return

        self.logln(f"Folder: {folder}")
        self.logln(f"Using config: {cfg}")
        self.logln(f"Found {len(wavs)} wav file(s).")
        self.logln("-" * 50)

        ok = 0
        for wpath in wavs:
            try:
                add_label_to_wav(wpath, cfg)
                self.logln(f"OK:   {os.path.basename(wpath)}")
                ok += 1
            except Exception as e:
                self.logln(f"FAIL: {os.path.basename(wpath)} -> {e}")

        self.logln("-" * 50)
        self.logln(f"Done. Success: {ok}/{len(wavs)}")
        messagebox.showinfo("Done", f"Processing finished.\nSuccess: {ok}/{len(wavs)}")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()