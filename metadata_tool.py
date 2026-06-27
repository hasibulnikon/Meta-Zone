import customtkinter as ctk
from tkinter import filedialog, messagebox
import csv, subprocess, os, sys, threading, datetime, json

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ── Colors ─────────────────────────────────────────────────────────────
BG   = "#050724"   # darkest blue
BG2  = "#1b1b29"   # card bg
BG3  = "#090b1c"   # header / input bg
BG4  = "#030518"   # titlebar / statusbar
TXT  = "#e8e8f4"
TXT2 = "#9a9ab8"
TXT3 = "#4a4a68"
GRN  = "#4dbe62"   # bright green accent
GBNB = "#369641"   # main green
GBNB2= "#2a7834"   # hover green
RED  = "#f07878"
RED2 = "#1e0d0d"
AMB  = "#f5c842"
AMB2 = "#1e1800"
BLU  = "#5b9ef5"
BDR  = "#141638"
LOG_BG = "#030416"

# ── Helpers ────────────────────────────────────────────────────────────
def find_exiftool():
    if getattr(sys,'frozen',False):
        base = sys._MEIPASS
        b = os.path.join(base,'exiftool_pkg','exiftool.exe')
        if os.path.exists(b): return b
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    for n in ['exiftool.exe','exiftool']:
        p = os.path.join(base,n)
        if os.path.exists(p): return p
    for d in os.environ.get('PATH','').split(os.pathsep):
        for n in ['exiftool.exe','exiftool']:
            p = os.path.join(d,n)
            if os.path.exists(p): return p
    return None

def find_file(folder, name, match_ext):
    exact = os.path.join(folder, name)
    if os.path.exists(exact): return exact
    if match_ext:
        base = os.path.splitext(name)[0]
        try:
            for f in os.listdir(folder):
                if os.path.splitext(f)[0].lower() == base.lower():
                    return os.path.join(folder, f)
        except: pass
    return None

def find_recursive(folder, name, match_ext):
    r = find_file(folder, name, match_ext)
    if r: return r
    try:
        for root, dirs, files in os.walk(folder):
            if root == folder: continue
            r = find_file(root, name, match_ext)
            if r: return r
    except: pass
    return None

def prefs_path():
    base = os.path.dirname(sys.executable) if getattr(sys,'frozen',False) \
        else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base,'prefs.json')

def load_prefs():
    try:
        with open(prefs_path()) as f: return json.load(f)
    except: return {'csv':[],'folders':[]}

def save_prefs(p):
    try:
        with open(prefs_path(),'w') as f: json.dump(p,f,indent=2)
    except: pass

def add_recent(prefs, key, val, limit=5):
    lst = prefs.get(key,[])
    if val in lst: lst.remove(val)
    lst.insert(0,val); prefs[key]=lst[:limit]; save_prefs(prefs)

# ── App ────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Meta Zone")
        self.configure(fg_color=BG)
        self.resizable(True, True)

        self.csv_rows     = []
        self.csv_headers  = []
        self.running      = False
        self.last_summary = ""
        self.last_folder  = ""
        self.prefs        = load_prefs()

        self.csv_path_var    = ctk.StringVar()
        self.folder_path_var = ctk.StringVar()
        self.col_file_var    = ctk.StringVar(value="(skip)")
        self.col_title_var   = ctk.StringVar(value="(skip)")
        self.col_kw_var      = ctk.StringVar(value="(skip)")
        self.col_desc_var    = ctk.StringVar(value="(skip)")
        self.match_only_var  = ctk.BooleanVar(value=True)
        self.subfolder_var   = ctk.BooleanVar(value=True)
        self.rm_prog_var     = ctk.BooleanVar(value=True)

        self._load_icon()
        self._build_ui()
        self._center(920, 920)
        self.minsize(620, 620)
        self.after(200, self._check_et)

    def _load_icon(self):
        self._icon_ctk = None
        base = sys._MEIPASS if getattr(sys,'frozen',False) \
            else os.path.dirname(os.path.abspath(__file__))
        for n in ['icon.png','icon.ico']:
            p = os.path.join(base,n)
            if os.path.exists(p):
                try: self.iconbitmap(p)
                except: pass
                try:
                    from PIL import Image
                    img = Image.open(p).convert("RGBA").resize((32,32))
                    self._icon_ctk = ctk.CTkImage(img, size=(32,32))
                except: pass
                break

    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def ts(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    # ── UI BUILD ───────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_titlebar()
        self._build_body()
        self._build_statusbar()

    def _build_titlebar(self):
        tb = ctk.CTkFrame(self, fg_color=BG4, corner_radius=0, height=64)
        tb.grid(row=0, column=0, sticky="ew")
        tb.grid_propagate(False)
        tb.grid_columnconfigure(2, weight=1)

        if self._icon_ctk:
            ctk.CTkLabel(tb, image=self._icon_ctk, text="",
                fg_color=BG4).grid(row=0, column=0, padx=(16,10), pady=16)
        else:
            ctk.CTkLabel(tb, text=" M ",
                font=ctk.CTkFont("Segoe UI", 14, "bold"),
                fg_color=GBNB, text_color="white",
                corner_radius=8).grid(row=0, column=0, padx=(16,10), pady=16)

        ctk.CTkLabel(tb, text="Meta Zone",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=TXT, fg_color=BG4).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(tb, text="v0.5 Beta",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TXT3, fg_color=BG4).grid(
            row=0, column=2, sticky="w", padx=(8,0))

        cr = ctk.CTkFrame(tb, fg_color=BG4, corner_radius=0)
        cr.grid(row=0, column=3, padx=(0,18), pady=10, sticky="e")
        ctk.CTkLabel(cr, text="All Rights Reserved By",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=TXT3, fg_color=BG4).pack(anchor="e")
        ctk.CTkLabel(cr, text="© HASIBNIKON",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=TXT2, fg_color=BG4).pack(anchor="e")

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        # Left scrollable panel
        self._left = ctk.CTkScrollableFrame(body,
            fg_color=BG,
            scrollbar_button_color=BG3,
            scrollbar_button_hover_color=BDR,
            corner_radius=0)
        self._left.grid(row=0, column=0, sticky="nsew",
            padx=(14,6), pady=12)
        self._left.grid_columnconfigure(0, weight=1)

        self._build_action_row()
        self._build_csv_card()
        self._build_folder_card()
        self._build_map_card()

        # Right log panel — fixed 210px
        log_outer = ctk.CTkFrame(body, fg_color=BG2,
            corner_radius=20, border_width=1,
            border_color=BDR, width=200)
        log_outer.grid(row=0, column=1, sticky="nsew",
            padx=(0,10), pady=10)
        log_outer.grid_propagate(False)
        log_outer.grid_rowconfigure(1, weight=1)
        log_outer.grid_columnconfigure(0, weight=1)
        self._build_log_panel(log_outer)

    def _build_action_row(self):
        row = ctk.CTkFrame(self._left, fg_color=BG, corner_radius=0)
        row.pack(fill="x", pady=(0,10))
        row.grid_columnconfigure(0, weight=1)

        self.embed_btn = ctk.CTkButton(row,
            text="▶  Start Embedding",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            fg_color=GBNB, hover_color=GBNB2,
            text_color="white", height=54,
            corner_radius=27, command=self.start_embed)
        self.embed_btn.grid(row=0, column=0, sticky="ew")

        self.reset_btn = ctk.CTkButton(row,
            text="↺", width=54, height=54,
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            fg_color=RED2, hover_color="#3d1515",
            text_color=RED, corner_radius=27,
            command=self.reset_all)
        self.reset_btn.grid(row=0, column=1, padx=(8,0))

        self.save_log_btn = ctk.CTkButton(row,
            text="💾  Save Log", width=130, height=54,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=BG3, hover_color=BDR,
            text_color=TXT2, corner_radius=27,
            command=self.export_log)
        self.save_log_btn.grid(row=0, column=2, padx=(8,0))

    def _card_frame(self):
        f = ctk.CTkFrame(self._left, fg_color=BG2,
            corner_radius=20, border_width=1, border_color=BDR)
        f.pack(fill="x", pady=(0,10))
        f.grid_columnconfigure(0, weight=1)
        return f

    def _card_header(self, parent, num, title, browse_cmd=None):
        hdr = ctk.CTkFrame(parent, fg_color=BG3,
            corner_radius=20, height=50)
        hdr.pack(fill="x")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        # Full circle badge
        ctk.CTkLabel(hdr, text=str(num),
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=GBNB, text_color="white",
            corner_radius=60,
            width=30, height=30).grid(
            row=0, column=0, padx=(14,10), pady=7)

        ctk.CTkLabel(hdr, text=title,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=TXT2, fg_color=BG3).grid(
            row=0, column=1, sticky="w")

        if browse_cmd:
            ctk.CTkButton(hdr, text="Browse",
                width=95, height=32,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                fg_color=GBNB, hover_color=GBNB2,
                text_color="white", corner_radius=20,
                command=browse_cmd).grid(
                row=0, column=2, padx=(0,12), pady=9)

    def _switch(self, parent, text, var):
        return ctk.CTkSwitch(parent,
            text=text,
            variable=var,
            font=ctk.CTkFont("Segoe UI", 12),
            progress_color=GBNB,
            button_color=TXT,
            button_hover_color="#ccccff",
            text_color=GRN,
            fg_color=BDR,
            onvalue=True, offvalue=False,
            width=56, height=28)

    def _build_csv_card(self):
        card = self._card_frame()
        self._card_header(card, "1", "Load CSV", self.load_csv)

        body = ctk.CTkFrame(card, fg_color=BG2, corner_radius=0)
        body.pack(fill="x", padx=14, pady=(10,12))
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(body,
            textvariable=self.csv_path_var,
            state="readonly", height=40,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=BG3, text_color=TXT,
            border_color=BDR, corner_radius=20).pack(
            fill="x", pady=(0,10))

        row = ctk.CTkFrame(body, fg_color=BG2, corner_radius=0)
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1)

        self.csv_badge = ctk.CTkLabel(row,
            text="No CSV loaded",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color=BG3, text_color=TXT3,
            corner_radius=20, padx=12, pady=5)
        self.csv_badge.grid(row=0, column=0, sticky="w")

        self._switch(row, "Match Filename Only",
            self.match_only_var).grid(
            row=0, column=1, sticky="e", padx=(10,0))

    def _build_folder_card(self):
        card = self._card_frame()
        self._card_header(card, "2", "Image folder", self.browse_folder)

        body = ctk.CTkFrame(card, fg_color=BG2, corner_radius=0)
        body.pack(fill="x", padx=14, pady=(10,12))
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(body,
            textvariable=self.folder_path_var,
            state="readonly", height=40,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=BG3, text_color=TXT,
            border_color=BDR, corner_radius=20).pack(
            fill="x", pady=(0,10))

        row = ctk.CTkFrame(body, fg_color=BG2, corner_radius=0)
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1)

        self.folder_badge = ctk.CTkLabel(row,
            text="No folder selected",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color=BG3, text_color=TXT3,
            corner_radius=20, padx=12, pady=5)
        self.folder_badge.grid(row=0, column=0, sticky="w")

        self._switch(row, "Include Sub-Folders",
            self.subfolder_var).grid(
            row=0, column=1, sticky="e", padx=(10,0))

    def _build_map_card(self):
        card = self._card_frame()
        self._card_header(card, "3", "Map columns")

        body = ctk.CTkFrame(card, fg_color=BG2, corner_radius=0)
        body.pack(fill="x", padx=14, pady=(10,12))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(body,
            text="Auto-detected from column names.",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TXT3, fg_color=BG2).grid(
            row=0, column=0, columnspan=2,
            sticky="w", pady=(0,10))

        self.col_combos = {}
        fields = [
            ("FILENAME", self.col_file_var),
            ("TITLE",    self.col_title_var),
            ("KEYWORDS", self.col_kw_var),
            ("DESCRIPTION", self.col_desc_var),
        ]
        for i, (lbl, var) in enumerate(fields):
            r = (i // 2) + 1
            c = i % 2
            cell = ctk.CTkFrame(body, fg_color=BG2, corner_radius=0)
            cell.grid(row=r, column=c, sticky="ew",
                padx=(0 if c==0 else 8, 0), pady=5)
            cell.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(cell, text=lbl,
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
                text_color=TXT3, fg_color=BG2).pack(anchor="w")
            cb = ctk.CTkComboBox(cell,
                variable=var,
                values=["(skip)"],
                state="readonly",
                font=ctk.CTkFont("Segoe UI", 12),
                fg_color=BG3,
                text_color=TXT,
                border_color=BDR,
                button_color=GBNB,
                button_hover_color=GBNB2,
                dropdown_fg_color=BG4,
                dropdown_text_color=TXT,
                dropdown_hover_color=GBNB2,
                corner_radius=20,
                height=38,
                command=lambda v: self._update_match())
            cb.pack(fill="x", pady=(4,0))
            self.col_combos[lbl] = cb

        # Separator
        ctk.CTkFrame(body, fg_color=BDR, height=1,
            corner_radius=0).grid(
            row=3, column=0, columnspan=2,
            sticky="ew", pady=(14,10))

        # Remove Program Name
        rm = ctk.CTkFrame(body, fg_color=BG3, corner_radius=20)
        rm.grid(row=4, column=0, columnspan=2,
            sticky="ew", pady=(0,4))
        rm.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(rm, fg_color=BG3, corner_radius=0)
        info.grid(row=0, column=0, sticky="w", padx=14, pady=12)
        ctk.CTkLabel(info, text="Remove Program Name",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=TXT2, fg_color=BG3).pack(anchor="w")
        ctk.CTkLabel(info,
            text="Clears upscaler/software name from metadata",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TXT3, fg_color=BG3).pack(anchor="w")

        self._switch(rm, "On",
            self.rm_prog_var).grid(
            row=0, column=1, padx=(0,14), pady=12)

    def _build_log_panel(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color=BG3,
            corner_radius=20, height=44)
        hdr.grid(row=0, column=0, sticky="ew",
            padx=8, pady=(8,4))
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr, text="ACTIVITY LOG",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=TXT3, fg_color=BG3).grid(
            row=0, column=0, sticky="w", padx=12)

        ctk.CTkButton(hdr, text="Clear",
            width=58, height=28,
            font=ctk.CTkFont("Segoe UI", 10),
            fg_color=BG4, hover_color=BDR,
            text_color=TXT3, corner_radius=20,
            command=self.clear_log).grid(
            row=0, column=1, padx=(0,8))

        self.log_text = ctk.CTkTextbox(parent,
            font=ctk.CTkFont("Consolas", 11),
            fg_color=LOG_BG, text_color=TXT,
            corner_radius=20, wrap="word",
            state="disabled",
            scrollbar_button_color=BG3,
            scrollbar_button_hover_color=BDR)
        self.log_text.grid(row=1, column=0, sticky="nsew",
            padx=8, pady=(0,8))

    def _build_statusbar(self):
        sb = ctk.CTkFrame(self, fg_color=BG4,
            corner_radius=0, height=46)
        sb.grid(row=2, column=0, sticky="ew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(4, weight=1)

        self.p_ok = ctk.CTkLabel(sb,
            text="✓  0 embedded",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="#0d2018", text_color=GRN,
            corner_radius=20, padx=12, pady=4)
        self.p_ok.grid(row=0, column=0, padx=(14,6), pady=10)

        self.p_warn = ctk.CTkLabel(sb,
            text="⚠  0 not found",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color=AMB2, text_color=AMB,
            corner_radius=20, padx=12, pady=4)
        self.p_warn.grid(row=0, column=1, padx=6, pady=10)

        self.p_err = ctk.CTkLabel(sb,
            text="✗  0 errors",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color=RED2, text_color=RED,
            corner_radius=20, padx=12, pady=4)
        self.p_err.grid(row=0, column=2, padx=6, pady=10)

        self.sb_status = ctk.CTkLabel(sb, text="",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=BLU, fg_color=BG4)
        self.sb_status.grid(row=0, column=3, padx=(10,0), sticky="w")

        self.sb_prog = ctk.CTkProgressBar(sb,
            progress_color=GRN, fg_color=BG3,
            height=7, corner_radius=4, width=110)
        self.sb_prog.grid(row=0, column=5, padx=(0,6))
        self.sb_prog.set(0)

        self.sb_pct = ctk.CTkLabel(sb, text="",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TXT2, fg_color=BG4)
        self.sb_pct.grid(row=0, column=6, padx=(0,10))

        self.sb_et = ctk.CTkLabel(sb,
            text="ExifTool · checking…",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TXT3, fg_color=BG4)
        self.sb_et.grid(row=0, column=7, padx=(0,16))

    # ── Log ────────────────────────────────────────────────────────────
    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{self.ts()}   {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def export_log(self):
        content = self.log_text.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Save Log", "Log is empty.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text","*.txt")],
            initialfile=f"metazone_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if path:
            with open(path,'w',encoding='utf-8') as f: f.write(content)
            self.log(f"✓  Log saved → {os.path.basename(path)}")

    def set_status(self, msg, color=None):
        self.sb_status.configure(text=msg, text_color=color or TXT3)

    def _check_et(self):
        et = find_exiftool()
        if et:
            self.log("✓  ExifTool ready")
            self.sb_et.configure(text="ExifTool · ready", text_color=GRN)
        else:
            self.log("⚠  ExifTool not found — place exiftool.exe next to this app")
            self.sb_et.configure(text="ExifTool · missing", text_color=RED)

    # ── CSV ────────────────────────────────────────────────────────────
    def load_csv(self):
        p = filedialog.askopenfilename(title="Select CSV",
            filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self._do_load_csv(p)

    def _do_load_csv(self, path):
        try:
            with open(path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.csv_rows = list(reader)
                self.csv_headers = list(reader.fieldnames or [])
            self.csv_path_var.set(path)
            self.csv_badge.configure(
                text=f"🗂  {len(self.csv_rows)} rows · {len(self.csv_headers)} columns",
                fg_color=GBNB2, text_color=GRN)
            self.log(f"✓  CSV — {len(self.csv_rows)} rows · {os.path.basename(path)}")
            self.set_status(f"CSV: {len(self.csv_rows)} rows", GRN)
            add_recent(self.prefs,'csv',path)
            self._update_combos()
            self._update_match()
        except Exception as e:
            messagebox.showerror("CSV Error", str(e))

    def _update_combos(self):
        opts = ["(skip)"] + self.csv_headers
        hints = {
            "FILENAME":    ["filename","file","name","image"],
            "TITLE":       ["title"],
            "KEYWORDS":    ["keyword","tag","kw"],
            "DESCRIPTION": ["desc","caption","description"],
        }
        vmap = {
            "FILENAME":    self.col_file_var,
            "TITLE":       self.col_title_var,
            "KEYWORDS":    self.col_kw_var,
            "DESCRIPTION": self.col_desc_var,
        }
        for lbl, cb in self.col_combos.items():
            cb.configure(values=opts)
            g = next((c for h in hints.get(lbl,[])
                for c in self.csv_headers if h in c.lower()), "")
            vmap[lbl].set(g or "(skip)")

    # ── Folder ─────────────────────────────────────────────────────────
    def browse_folder(self):
        p = filedialog.askdirectory(title="Select image folder")
        if p: self._do_set_folder(p)

    def _do_set_folder(self, path):
        self.folder_path_var.set(path)
        self.last_folder = path
        add_recent(self.prefs,'folders',path)
        self._update_match()
        self.log(f"✓  Folder set — {path}")

    def _update_match(self):
        folder = self.folder_path_var.get()
        col_f  = self.col_file_var.get()
        if not folder or not self.csv_rows or not col_f or col_f == "(skip)":
            return
        finder = find_recursive if self.subfolder_var.get() else find_file
        matched = sum(1 for row in self.csv_rows
            if finder(folder, (row.get(col_f) or "").strip(),
                self.match_only_var.get()))
        total = len(self.csv_rows)
        color = GRN if matched == total else AMB if matched > 0 else RED
        bg    = GBNB2 if matched == total else AMB2
        self.folder_badge.configure(
            text=f"📁  {matched} of {total} matched",
            fg_color=bg, text_color=color)
        self.set_status(f"{matched}/{total} files matched", color)

    # ── Reset ──────────────────────────────────────────────────────────
    def reset_all(self):
        if self.running:
            messagebox.showwarning("Busy", "Wait for current job to finish.")
            return
        if not messagebox.askyesno("Reset", "Clear everything and start fresh?"):
            return
        self.csv_path_var.set("")
        self.folder_path_var.set("")
        for v in [self.col_file_var, self.col_title_var,
                  self.col_kw_var, self.col_desc_var]:
            v.set("(skip)")
        self.csv_rows = []; self.csv_headers = []
        self.csv_badge.configure(
            text="No CSV loaded", fg_color=BG3, text_color=TXT3)
        self.folder_badge.configure(
            text="No folder selected", fg_color=BG3, text_color=TXT3)
        for cb in self.col_combos.values():
            cb.configure(values=["(skip)"])
        self.sb_prog.set(0); self.sb_pct.configure(text="")
        self.p_ok.configure(text="✓  0 embedded")
        self.p_warn.configure(text="⚠  0 not found")
        self.p_err.configure(text="✗  0 errors")
        self.embed_btn.configure(
            text="▶   Embed Metadata Now", state="normal")
        self.clear_log()
        self.log("↺  Reset — ready for new batch")
        if self.last_summary:
            self.set_status(f"Last: {self.last_summary}", TXT3)
        else:
            self.set_status("", TXT3)

    # ── Embed ──────────────────────────────────────────────────────────
    def start_embed(self):
        if self.running: return
        et = find_exiftool()
        if not et:
            messagebox.showerror("ExifTool not found",
                "Place exiftool.exe next to this app.\nhttps://exiftool.org")
            return
        if not self.csv_rows:
            messagebox.showerror("No CSV","Load a CSV first."); return
        if not self.folder_path_var.get():
            messagebox.showerror("No folder","Select image folder."); return
        fc = self.col_file_var.get()
        if not fc or fc == "(skip)":
            messagebox.showerror("Column missing",
                "Select the filename column."); return
        self.running = True
        self.embed_btn.configure(state="disabled", text="⟳   Processing...")
        threading.Thread(
            target=self._embed_thread, args=(et,), daemon=True).start()

    def _embed_thread(self, et):
        folder  = self.folder_path_var.get()
        col_f   = self.col_file_var.get()
        col_t   = self.col_title_var.get()
        col_k   = self.col_kw_var.get()
        col_d   = self.col_desc_var.get()
        use_sub = self.subfolder_var.get()
        use_ext = self.match_only_var.get()
        rm_prog = self.rm_prog_var.get()
        total   = len(self.csv_rows)
        ok = skipped = errors = 0
        finder  = find_recursive if use_sub else find_file

        self.after(0, lambda: self.log(f"▶  Batch started — {total} rows"))

        for i, row in enumerate(self.csv_rows):
            fn = (row.get(col_f) or "").strip()
            if not fn:
                skipped += 1
                self.after(0, lambda n=i+1,t=total,o=ok,s=skipped,e=errors:
                    self._prog(n,t,o,s,e))
                continue

            fp = finder(folder, fn, use_ext)
            if not fp:
                skipped += 1
                self.after(0, lambda f=fn:
                    self.log(f"⚠  Not found: {f}"))
                self.after(0, lambda n=i+1,t=total,o=ok,s=skipped,e=errors:
                    self._prog(n,t,o,s,e))
                continue

            cmd = [et,'-overwrite_original','-codedcharacterset=UTF8']
            title  = (row.get(col_t) or "").strip() if col_t and col_t!="(skip)" else ""
            kw_raw = (row.get(col_k) or "").strip() if col_k and col_k!="(skip)" else ""
            desc   = (row.get(col_d) or "").strip() if col_d and col_d!="(skip)" else ""

            if title:
                cmd += [f'-Title={title}',f'-ObjectName={title}',f'-Headline={title}']
            if kw_raw:
                for kw in [k.strip() for k in
                           kw_raw.replace(';',',').split(',') if k.strip()]:
                    cmd += [f'-Keywords={kw}',f'-Subject={kw}']
            if desc:
                cmd += [f'-Description={desc}',f'-Caption-Abstract={desc}']
            if rm_prog:
                cmd += ['-Software=','-CreatorTool=','-HistorySoftwareAgent=']
            cmd.append(fp)

            try:
                flags = subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0
                res = subprocess.run(cmd, capture_output=True, text=True,
                    timeout=30, creationflags=flags)
                actual = os.path.basename(fp)
                if res.returncode == 0:
                    ok += 1
                    self.after(0, lambda fn=actual:
                        self.log(f"✓  {fn}"))
                else:
                    errors += 1
                    err = (res.stderr or res.stdout or "Unknown").strip()
                    self.after(0, lambda fn=actual, e=err:
                        self.log(f"✗  {fn} — {e}"))
            except Exception as ex:
                errors += 1
                self.after(0, lambda fn=fn, e=str(ex):
                    self.log(f"✗  {fn} — {e}"))

            self.after(0, lambda n=i+1,t=total,o=ok,s=skipped,e=errors:
                self._prog(n,t,o,s,e))

        summary = f"{ok} embedded · {skipped} not found · {errors} errors"
        self.last_summary = summary
        self.after(0, lambda: (
            self.log(f"● Done — {summary}"),
            self.set_status(f"Done — {summary}", GRN),
            self.embed_btn.configure(
                state="normal", text="▶  Start Again"),
            setattr(self,'running',False)
        ))

    def _prog(self, n, t, ok, skipped, errors):
        pct = n / t if t else 0
        self.sb_prog.set(pct)
        self.sb_pct.configure(text=f"{int(pct*100)}%")
        self.set_status(f"Processing {n} of {t}...", BLU)
        self.p_ok.configure(text=f"✓  {ok} embedded")
        self.p_warn.configure(text=f"⚠  {skipped} not found")
        self.p_err.configure(text=f"✗  {errors} errors")

if __name__ == '__main__':
    app = App()
    app.mainloop()
