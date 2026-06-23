import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv, subprocess, os, sys, threading, datetime, json

# ── Helpers ────────────────────────────────────────────────────────────
def find_exiftool():
    if getattr(sys,'frozen',False):
        base=sys._MEIPASS
        b=os.path.join(base,'exiftool_pkg','exiftool.exe')
        if os.path.exists(b): return b
    else:
        base=os.path.dirname(os.path.abspath(__file__))
    for n in ['exiftool.exe','exiftool']:
        p=os.path.join(base,n)
        if os.path.exists(p): return p
    for d in os.environ.get('PATH','').split(os.pathsep):
        for n in ['exiftool.exe','exiftool']:
            p=os.path.join(d,n)
            if os.path.exists(p): return p
    return None

def find_file(folder, csv_name, match_ext_only):
    exact=os.path.join(folder,csv_name)
    if os.path.exists(exact): return exact
    if match_ext_only:
        base=os.path.splitext(csv_name)[0]
        try:
            for f in os.listdir(folder):
                if os.path.splitext(f)[0].lower()==base.lower():
                    return os.path.join(folder,f)
        except: pass
    return None

def find_file_recursive(folder, csv_name, match_ext_only):
    result=find_file(folder,csv_name,match_ext_only)
    if result: return result
    try:
        for root,dirs,files in os.walk(folder):
            if root==folder: continue
            result=find_file(root,csv_name,match_ext_only)
            if result: return result
    except: pass
    return None

def prefs_path():
    base=os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base,'prefs.json')

def load_prefs():
    try:
        with open(prefs_path()) as f: return json.load(f)
    except: return {'csv':[],'folders':[]}

def save_prefs(p):
    try:
        with open(prefs_path(),'w') as f: json.dump(p,f,indent=2)
    except: pass

def add_recent(prefs,key,val,limit=5):
    lst=prefs.get(key,[])
    if val in lst: lst.remove(val)
    lst.insert(0,val); prefs[key]=lst[:limit]; save_prefs(prefs)

# ── Colors ─────────────────────────────────────────────────────────────
BG  ='#141412'; BG2 ='#1a1a18'; BG3 ='#222220'; BG4 ='#0e0e0c'
TXT ='#e8e8e4'; TXT2='#9a9a96'; TXT3='#4a4a48'
GRN ='#4caf72'; GRN2='#1a3020'; GRN3='#2a4830'
GBNB='#2d7a4f'; GBNB2='#1e5c3a'
RED ='#e87070'; RED2='#2a1a1a'; RED3='#4a2828'
AMB ='#f0c060'; AMB2='#2a2010'; AMB3='#4a3818'
BLU ='#3b8fe8'
BDR ='#2a2a28'; BDR2='#3a3a38'

class Toggle(tk.Frame):
    """Pill-style on/off toggle matching the template."""
    def __init__(self, parent, text, var, bg=GRN2, fg=GRN, border=GRN3, **kw):
        super().__init__(parent, bg=bg,
            highlightbackground=border, highlightthickness=1,
            padx=8, pady=3, cursor='hand2', **kw)
        self.var=var; self.fg=fg; self.bg_off=BG3; self.bg_on=bg
        self.border_on=border; self.border_off=BDR
        # Pill indicator
        self.dot=tk.Canvas(self,width=28,height=14,bg=bg,
            highlightthickness=0)
        self.dot.pack(side='left',padx=(0,6))
        self.lbl=tk.Label(self,text=text,font=('Segoe UI',9,'bold'),
            bg=bg,fg=fg,cursor='hand2')
        self.lbl.pack(side='left')
        self._draw()
        self.bind('<Button-1>',self._toggle)
        self.dot.bind('<Button-1>',self._toggle)
        self.lbl.bind('<Button-1>',self._toggle)
        var.trace_add('write',lambda *a: self._draw())

    def _draw(self):
        on=self.var.get()
        self.dot.delete('all')
        track=GBNB if on else BDR2
        self.dot.create_rounded_rect=self._rr
        self._rr(self.dot,1,2,27,12,6,fill=track)
        cx=20 if on else 8
        self.dot.create_oval(cx-5,2,cx+5,12,fill='white',outline='')
        bg=self.bg_on if on else self.bg_off
        fg=self.fg if on else TXT3
        self.configure(bg=bg,highlightbackground=self.border_on if on else self.border_off)
        self.dot.configure(bg=bg)
        self.lbl.configure(bg=bg,fg=fg)

    def _rr(self,canvas,x1,y1,x2,y2,r,**kw):
        canvas.create_arc(x1,y1,x1+2*r,y1+2*r,start=90,extent=90,style='pieslice',outline='',**kw)
        canvas.create_arc(x2-2*r,y1,x2,y1+2*r,start=0,extent=90,style='pieslice',outline='',**kw)
        canvas.create_arc(x1,y2-2*r,x1+2*r,y2,start=180,extent=90,style='pieslice',outline='',**kw)
        canvas.create_arc(x2-2*r,y2-2*r,x2,y2,start=270,extent=90,style='pieslice',outline='',**kw)
        canvas.create_rectangle(x1+r,y1,x2-r,y2,outline='',**kw)
        canvas.create_rectangle(x1,y1+r,x2,y2-r,outline='',**kw)

    def _toggle(self,_=None):
        self.var.set(not self.var.get())

class Tip:
    def __init__(self,w,text):
        self.w=w; self.text=text; self.tip=None
        w.bind('<Enter>',self.show); w.bind('<Leave>',self.hide)
    def show(self,_=None):
        if self.tip or not self.text: return
        x=self.w.winfo_rootx()+16; y=self.w.winfo_rooty()+self.w.winfo_height()+4
        self.tip=tk.Toplevel(self.w); self.tip.wm_overrideredirect(True)
        self.tip.geometry(f'+{x}+{y}')
        tk.Label(self.tip,text=self.text,font=('Segoe UI',8),bg='#2a2a28',fg=TXT,
            padx=8,pady=4,wraplength=260,justify='left',
            highlightbackground=BDR2,highlightthickness=1).pack()
    def hide(self,_=None):
        if self.tip: self.tip.destroy(); self.tip=None

class App:
    def __init__(self,root):
        self.root=root
        self.root.title('Meta Zone')
        self.root.configure(bg=BG)
        self.root.resizable(True,True)
        self.root.minsize(500,520)

        self.csv_path   =tk.StringVar()
        self.folder_path=tk.StringVar()
        self.col_file   =tk.StringVar()
        self.col_title  =tk.StringVar()
        self.col_kw     =tk.StringVar()
        self.col_desc   =tk.StringVar()
        self.match_only =tk.BooleanVar(value=True)
        self.subfolder  =tk.BooleanVar(value=True)
        self.rm_program =tk.BooleanVar(value=False)
        self.csv_rows   =[]
        self.csv_headers=[]
        self.running    =False
        self.last_summary=''
        self.last_folder =''
        self.prefs=load_prefs()

        self._load_icon()
        self._style()
        self._build()
        self.root.update_idletasks()
        self._center(700,580)
        self._check_et()

    def _load_icon(self):
        self.icon_img=None
        base=sys._MEIPASS if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__))
        for n in ['icon.png','icon.ico']:
            p=os.path.join(base,n)
            if os.path.exists(p):
                try: self.root.iconbitmap(p)
                except: pass
                try:
                    from PIL import Image,ImageTk
                    img=Image.open(p).convert('RGBA').resize((28,28))
                    self.icon_img=ImageTk.PhotoImage(img)
                except:
                    try: self.icon_img=tk.PhotoImage(file=p)
                    except: pass
                break

    def _style(self):
        s=ttk.Style(); s.theme_use('clam')
        s.configure('TCombobox',fieldbackground=BG3,background=BG3,
            foreground=TXT,selectbackground=BLU,arrowcolor=TXT2,bordercolor=BDR)
        s.map('TCombobox',fieldbackground=[('readonly',BG3)],
            foreground=[('readonly',TXT)],bordercolor=[('focus',BLU)])
        s.configure('Vertical.TScrollbar',background=BG3,troughcolor=BG2,
            arrowcolor=TXT3,bordercolor=BDR)
        s.configure('G.Horizontal.TProgressbar',background=GRN,
            troughcolor=BG3,bordercolor=BDR)

    def _center(self,w,h):
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        self.root.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')

    def ts(self): return datetime.datetime.now().strftime('%H:%M:%S')

    # ── BUILD UI ───────────────────────────────────────────────────────
    def _build(self):
        # Titlebar
        tb=tk.Frame(self.root,bg=BG4,padx=14,pady=10)
        tb.pack(fill='x')
        if self.icon_img:
            tk.Label(tb,image=self.icon_img,bg=BG4).pack(side='left')
        else:
            tk.Label(tb,text=' M ',font=('Segoe UI',11,'bold'),
                bg=GBNB,fg='white',padx=4,pady=2).pack(side='left')
        tk.Label(tb,text='  Meta Zone',font=('Segoe UI',15,'bold'),
            bg=BG4,fg=TXT).pack(side='left')
        tk.Label(tb,text=' v2.1',font=('Segoe UI',9),
            bg=BG4,fg=TXT3).pack(side='left',padx=2)
        rc=tk.Frame(tb,bg=BG4); rc.pack(side='right')
        tk.Label(rc,text='All Rights Reserved By',font=('Segoe UI',8),
            bg=BG4,fg=TXT3).pack(anchor='e')
        tk.Label(rc,text='© HASIBNIKON',font=('Segoe UI',12,'bold'),
            bg=BG4,fg=TXT2).pack(anchor='e')

        # Body: left + mid-strip + log
        self.body=tk.Frame(self.root,bg=BG)
        self.body.pack(fill='both',expand=True)
        self.body.columnconfigure(0,weight=1)
        self.body.rowconfigure(0,weight=1)

        # Left scrollable panel
        lw=tk.Frame(self.body,bg=BG)
        lw.grid(row=0,column=0,sticky='nsew')
        lw.columnconfigure(0,weight=1); lw.rowconfigure(0,weight=1)

        self.cv=tk.Canvas(lw,bg=BG,highlightthickness=0)
        self.cv.grid(row=0,column=0,sticky='nsew')
        self.cv.bind('<Configure>',lambda e: self.cv.itemconfig(self._cwin,width=e.width))

        self.lpanel=tk.Frame(self.cv,bg=BG,padx=12,pady=10)
        self._cwin=self.cv.create_window((0,0),window=self.lpanel,anchor='nw')
        self.lpanel.bind('<Configure>',lambda e: self.cv.configure(
            scrollregion=self.cv.bbox('all')))
        self.lpanel.columnconfigure(0,weight=1)
        self.cv.bind_all('<MouseWheel>',lambda e: self.cv.yview_scroll(
            int(-1*(e.delta/120)),'units'))

        # Build left panel content
        self._build_embed_row()
        self._build_csv_card()
        self._build_folder_card()
        self._build_map_card()

        # Mid strip: scroll buttons
        mid=tk.Frame(self.body,bg=BG,width=30)
        mid.grid(row=0,column=1,sticky='ns')
        mid.pack_propagate(False); mid.grid_propagate(False)
        inner=tk.Frame(mid,bg=BG)
        inner.place(relx=0.5,rely=0.5,anchor='center')
        self.up_b=tk.Label(inner,text='▲',font=('Segoe UI',9,'bold'),
            bg=BG3,fg=TXT3,cursor='hand2',padx=6,pady=5,
            highlightbackground=BDR,highlightthickness=1)
        self.up_b.pack(pady=(0,6))
        self.up_b.bind('<Button-1>',lambda e: self.cv.yview_scroll(-3,'units'))
        self.dn_b=tk.Label(inner,text='▼',font=('Segoe UI',9,'bold'),
            bg=BG3,fg=TXT3,cursor='hand2',padx=6,pady=5,
            highlightbackground=BDR,highlightthickness=1)
        self.dn_b.pack()
        self.dn_b.bind('<Button-1>',lambda e: self.cv.yview_scroll(3,'units'))

        # Log panel — always visible, 210px
        self.log_panel=tk.Frame(self.body,bg=BG2,width=210)
        self.log_panel.grid(row=0,column=2,sticky='nsew')
        self.log_panel.grid_propagate(False)
        self.log_panel.columnconfigure(0,weight=1)
        self.log_panel.rowconfigure(1,weight=1)
        self._build_log()

        # Status bar
        self._build_sbar()

    def _build_embed_row(self):
        row=tk.Frame(self.lpanel,bg=BG,pady=4)
        row.pack(fill='x')
        row.columnconfigure(0,weight=1)
        self.embed_btn=tk.Button(row,text='▶   Embed Metadata Now',
            command=self.start_embed,
            font=('Segoe UI',13,'bold'),bg=GBNB,fg='white',
            relief='flat',pady=13,cursor='hand2',
            activebackground=GBNB2,activeforeground='white')
        self.embed_btn.grid(row=0,column=0,sticky='ew')
        self.reset_btn=tk.Button(row,text='↺',command=self.reset_all,
            font=('Segoe UI',14,'bold'),bg=RED2,fg=RED,
            relief='flat',padx=12,pady=12,cursor='hand2',
            activebackground=RED3,activeforeground='#ffaaaa',
            highlightbackground=RED3,highlightthickness=1)
        self.reset_btn.grid(row=0,column=1,padx=(6,0))
        Tip(self.reset_btn,'Reset all fields')
        self.exp_btn=tk.Button(row,text='📄',command=self.export_log,
            font=('Segoe UI',13),bg=BG3,fg=TXT2,
            relief='flat',padx=10,pady=12,cursor='hand2',
            activebackground=BDR2,activeforeground=TXT,
            highlightbackground=BDR,highlightthickness=1)
        self.exp_btn.grid(row=0,column=2,padx=(4,0))
        Tip(self.exp_btn,'Export activity log to TXT')

    def _card(self, step, title, has_browse=False, browse_cmd=None, browse_recent_attr=None):
        """Create a card. Returns (card_frame, body_frame)."""
        outer=tk.Frame(self.lpanel,bg=BG,pady=4)
        outer.pack(fill='x')
        outer.columnconfigure(0,weight=1)
        card=tk.Frame(outer,bg=BG2,highlightbackground=BDR,highlightthickness=1)
        card.pack(fill='x')
        card.columnconfigure(0,weight=1)
        # Header
        hdr=tk.Frame(card,bg=BG3)
        hdr.pack(fill='x')
        hdr.columnconfigure(0,weight=1)
        hdr_left=tk.Frame(hdr,bg=BG3,padx=12,pady=9)
        hdr_left.pack(side='left',fill='x',expand=True)
        tk.Label(hdr_left,text=f' {step} ',font=('Segoe UI',9,'bold'),
            bg=GBNB,fg='white').pack(side='left')
        tk.Label(hdr_left,text=f'  {title}',font=('Segoe UI',10,'bold'),
            bg=BG3,fg=TXT2).pack(side='left')
        if has_browse and browse_cmd:
            browse_wrap=tk.Frame(hdr,bg=GBNB)
            browse_wrap.pack(side='right',fill='y')
            tk.Button(browse_wrap,text=' Browse ',command=browse_cmd,
                font=('Segoe UI',10,'bold'),bg=GBNB,fg='white',
                relief='flat',padx=14,pady=0,cursor='hand2',
                activebackground=GBNB2,activeforeground='white',
                bd=0,highlightthickness=0).pack(fill='both',expand=True)
            if browse_recent_attr:
                mb=tk.Menubutton(browse_wrap,text='▾',font=('Segoe UI',9),
                    bg=GBNB2,fg='white',relief='flat',padx=6,
                    activebackground=GBNB,cursor='hand2',bd=0)
                mb.pack(side='right',fill='y')
                menu=tk.Menu(mb,tearoff=0,bg=BG3,fg=TXT,
                    activebackground=BLU,activeforeground='white')
                mb.configure(menu=menu)
                setattr(self,browse_recent_attr,menu)
        tk.Frame(card,bg=BDR,height=1).pack(fill='x')
        body=tk.Frame(card,bg=BG2,padx=12,pady=10)
        body.pack(fill='x')
        body.columnconfigure(0,weight=1)
        return body

    def _path_display(self, parent, var):
        f=tk.Frame(parent,bg=BG3,highlightbackground=BDR,highlightthickness=1)
        f.pack(fill='x',pady=(0,6))
        f.columnconfigure(0,weight=1)
        e=tk.Entry(f,textvariable=var,font=('Segoe UI',10),
            bg=BG3,fg=TXT,relief='flat',state='readonly',
            readonlybackground=BG3,highlightthickness=0)
        e.grid(row=0,column=0,sticky='ew',padx=8,pady=6)
        return e

    def _badge(self, parent, textvariable):
        lbl=tk.Label(parent,textvariable=textvariable,
            font=('Segoe UI',9,'bold'),
            bg=GRN2,fg=GRN,padx=10,pady=3,
            highlightbackground=GRN3,highlightthickness=1)
        return lbl

    def _build_csv_card(self):
        body=self._card('1','Load CSV',True,self.load_csv,'csv_menu')
        self._path_display(body,self.csv_path)
        row=tk.Frame(body,bg=BG2); row.pack(fill='x')
        self.csv_badge_var=tk.StringVar(value='No CSV loaded')
        self.csv_badge=tk.Label(row,textvariable=self.csv_badge_var,
            font=('Segoe UI',9,'bold'),bg=GRN2,fg=GRN,padx=10,pady=3,
            highlightbackground=GRN3,highlightthickness=1)
        self.csv_badge.pack(side='left')
        self.match_toggle=Toggle(row,text='Match Filename Only',var=self.match_only)
        self.match_toggle.pack(side='right')
        self._refresh_csv_menu()

    def _build_folder_card(self):
        body=self._card('2','Image folder',True,self.browse_folder,'folder_menu')
        self._path_display(body,self.folder_path)
        row=tk.Frame(body,bg=BG2); row.pack(fill='x')
        self.folder_badge_var=tk.StringVar(value='No folder selected')
        self.folder_badge=tk.Label(row,textvariable=self.folder_badge_var,
            font=('Segoe UI',9,'bold'),bg=GRN2,fg=GRN,padx=10,pady=3,
            highlightbackground=GRN3,highlightthickness=1)
        self.folder_badge.pack(side='left')
        self.subfolder_toggle=Toggle(row,text='Include Sub-Folders',var=self.subfolder)
        self.subfolder_toggle.pack(side='right')
        self._refresh_folder_menu()

    def _build_map_card(self):
        body=self._card('3','Map columns')
        tk.Label(body,text='Auto-detected. Hover labels for info.',
            font=('Segoe UI',8),bg=BG2,fg=TXT3,anchor='w').pack(fill='x',pady=(0,8))
        self.col_combos={}
        fields=[('FILENAME',self.col_file,'Column with image filename. Extension can differ.'),
                ('TITLE',self.col_title,'Short title for Adobe Stock (max 200 chars).'),
                ('KEYWORDS',self.col_kw,'Comma/semicolon separated. 7–50 recommended.'),
                ('DESCRIPTION',self.col_desc,'Longer caption or description.')]
        grid=tk.Frame(body,bg=BG2); grid.pack(fill='x')
        grid.columnconfigure(0,weight=1); grid.columnconfigure(1,weight=1)
        for i,(lbl,var,tip) in enumerate(fields):
            col=i%2; rn=i//2
            cell=tk.Frame(grid,bg=BG2,padx=3,pady=3)
            cell.grid(row=rn,column=col,sticky='ew',padx=3)
            cell.columnconfigure(0,weight=1)
            l=tk.Label(cell,text=lbl,font=('Segoe UI',8,'bold'),
                bg=BG2,fg=TXT3,anchor='w',cursor='question_arrow')
            l.pack(fill='x')
            Tip(l,tip)
            cb=ttk.Combobox(cell,textvariable=var,state='readonly',font=('Segoe UI',9))
            cb.pack(fill='x',ipady=3)
            cb.bind('<<ComboboxSelected>>',lambda e: self._update_match())
            self.col_combos[lbl]=cb
        # Remove Program Name toggle
        sep=tk.Frame(body,bg=BDR,height=1); sep.pack(fill='x',pady=(10,6))
        rm_row=tk.Frame(body,bg=BG3,highlightbackground=BDR,highlightthickness=1,
            padx=10,pady=8)
        rm_row.pack(fill='x')
        rm_row.columnconfigure(0,weight=1)
        tl=tk.Frame(rm_row,bg=BG3); tl.grid(row=0,column=0,sticky='w')
        tk.Label(tl,text='Remove Program Name',font=('Segoe UI',10,'bold'),
            bg=BG3,fg=TXT2).pack(anchor='w')
        tk.Label(tl,text='Clears upscaler/software name from metadata',
            font=('Segoe UI',8),bg=BG3,fg=TXT3).pack(anchor='w')
        Toggle(rm_row,text='On',var=self.rm_program,
            bg=GRN2,fg=GRN,border=GRN3).grid(row=0,column=1,sticky='e')

    def _build_log(self):
        hdr=tk.Frame(self.log_panel,bg=BG3)
        hdr.grid(row=0,column=0,sticky='ew')
        ih=tk.Frame(hdr,bg=BG3,padx=10,pady=8)
        ih.pack(fill='x')
        tk.Label(ih,text='ACTIVITY LOG',font=('Segoe UI',9,'bold'),
            bg=BG3,fg=TXT3).pack(side='left')
        tk.Button(ih,text='Clear',command=self.clear_log,
            font=('Segoe UI',8),bg=BG4,fg=TXT3,relief='flat',
            padx=6,pady=2,cursor='hand2',
            activebackground=BG3,activeforeground=TXT2).pack(side='right')
        tk.Frame(hdr,bg=BDR,height=1).pack(fill='x')
        lf=tk.Frame(self.log_panel,bg=BG2)
        lf.grid(row=1,column=0,sticky='nsew')
        self.log_text=tk.Text(lf,font=('Consolas',9),bg=BG2,fg=TXT,
            relief='flat',state='disabled',wrap='word',padx=8,pady=6)
        vsb=ttk.Scrollbar(lf,command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right',fill='y')
        self.log_text.pack(fill='both',expand=True)
        self.log_text.tag_config('ok',  foreground=GRN)
        self.log_text.tag_config('warn',foreground=AMB)
        self.log_text.tag_config('err', foreground=RED)
        self.log_text.tag_config('info',foreground=BLU)
        self.log_text.tag_config('ts',  foreground=TXT3)

    def _build_sbar(self):
        sb=tk.Frame(self.root,bg=BG4,highlightbackground=BDR,highlightthickness=1)
        sb.pack(fill='x',side='bottom')
        inner=tk.Frame(sb,bg=BG4,padx=10,pady=5); inner.pack(fill='x')
        pf=tk.Frame(inner,bg=BG4); pf.pack(side='left')
        self.p_ok  =self._pill(pf,'0 embedded',GRN2,GRN,GRN3)
        self.p_warn=self._pill(pf,'0 not found',AMB2,AMB,AMB3)
        self.p_err =self._pill(pf,'0 errors',RED2,RED,RED3)
        self.sb_et=tk.Label(inner,text='ExifTool · checking…',
            font=('Segoe UI',8),bg=BG4,fg=TXT3)
        self.sb_et.pack(side='right')
        self.sb_prog=ttk.Progressbar(inner,mode='determinate',length=80,
            style='G.Horizontal.TProgressbar')
        self.sb_prog.pack(side='right',padx=(0,8))
        self.sb_status=tk.Label(inner,text='',font=('Segoe UI',9),
            bg=BG4,fg=TXT3,anchor='w')
        self.sb_status.pack(side='right',padx=(0,10))

    def _pill(self,p,t,bg,fg,bd):
        l=tk.Label(p,text=t,font=('Segoe UI',8,'bold'),bg=bg,fg=fg,
            padx=8,pady=3,highlightbackground=bd,highlightthickness=1)
        l.pack(side='left',padx=2); return l

    # ── Recent menus ───────────────────────────────────────────────────
    def _refresh_csv_menu(self):
        self.csv_menu.delete(0,'end')
        for p in self.prefs.get('csv',[]):
            self.csv_menu.add_command(label=os.path.basename(p),
                command=lambda v=p: self._do_load_csv(v))
        if not self.prefs.get('csv'):
            self.csv_menu.add_command(label='No recent files',state='disabled')

    def _refresh_folder_menu(self):
        self.folder_menu.delete(0,'end')
        for p in self.prefs.get('folders',[]):
            self.folder_menu.add_command(label=p,
                command=lambda v=p: self._do_set_folder(v))
        if not self.prefs.get('folders'):
            self.folder_menu.add_command(label='No recent folders',state='disabled')

    # ── Logging ────────────────────────────────────────────────────────
    def log(self,msg,tag=''):
        self.log_text.configure(state='normal')
        self.log_text.insert('end',f'{self.ts()}  ','ts')
        self.log_text.insert('end',msg+'\n',tag)
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def clear_log(self):
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0','end')
        self.log_text.configure(state='disabled')

    def export_log(self):
        content=self.log_text.get('1.0','end').strip()
        if not content: messagebox.showinfo('Export','Log is empty.'); return
        path=filedialog.asksaveasfilename(defaultextension='.txt',
            filetypes=[('Text','*.txt')],
            initialfile=f'metazone_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        if path:
            with open(path,'w',encoding='utf-8') as f: f.write(content)
            self.log(f'✓  Log saved → {os.path.basename(path)}','ok')

    def set_status(self,msg,fg=None):
        self.sb_status.configure(text=msg,fg=fg or TXT3)

    def _check_et(self):
        et=find_exiftool()
        if et:
            self.log('✓  ExifTool ready','ok')
            self.sb_et.configure(text='ExifTool · ready',fg=GRN)
        else:
            self.log('⚠  ExifTool not found','warn')
            self.sb_et.configure(text='ExifTool · missing',fg=RED)

    # ── CSV ────────────────────────────────────────────────────────────
    def load_csv(self):
        p=filedialog.askopenfilename(title='Select CSV',
            filetypes=[('CSV','*.csv'),('All','*.*')])
        if p: self._do_load_csv(p)

    def _do_load_csv(self,path):
        try:
            with open(path,newline='',encoding='utf-8-sig') as f:
                r=csv.DictReader(f)
                self.csv_rows=list(r)
                self.csv_headers=list(r.fieldnames or [])
            self.csv_path.set(path)
            self.csv_badge_var.set(f'✓  {len(self.csv_rows)} rows · {len(self.csv_headers)} columns')
            self.csv_badge.configure(bg=GRN2,fg=GRN,highlightbackground=GRN3)
            self.log(f'✓  CSV loaded — {len(self.csv_rows)} rows · {os.path.basename(path)}','ok')
            self.set_status(f'CSV: {len(self.csv_rows)} rows',GRN)
            add_recent(self.prefs,'csv',path)
            self._refresh_csv_menu()
            self._update_combos()
            self._update_match()
        except Exception as e:
            messagebox.showerror('CSV Error',str(e))

    def _update_combos(self):
        opts=['(skip)']+self.csv_headers
        hints={'FILENAME':['filename','file','name','image'],
               'TITLE':['title'],'KEYWORDS':['keyword','tag','kw'],
               'DESCRIPTION':['desc','caption','description']}
        vmap={'FILENAME':self.col_file,'TITLE':self.col_title,
              'KEYWORDS':self.col_kw,'DESCRIPTION':self.col_desc}
        for lbl,cb in self.col_combos.items():
            cb['values']=opts
            g=next((c for h in hints.get(lbl,[])
                for c in self.csv_headers if h in c.lower()),'')
            vmap[lbl].set(g or '(skip)')

    # ── Folder ─────────────────────────────────────────────────────────
    def browse_folder(self):
        p=filedialog.askdirectory(title='Select image folder')
        if p: self._do_set_folder(p)

    def _do_set_folder(self,path):
        self.folder_path.set(path)
        self.last_folder=path
        add_recent(self.prefs,'folders',path)
        self._refresh_folder_menu()
        self._update_match()
        self.log(f'✓  Folder set — {path}','ok')

    def _update_match(self):
        folder=self.folder_path.get()
        col_f=self.col_file.get()
        if not folder or not self.csv_rows or not col_f or col_f=='(skip)':
            return
        fn=find_file_recursive if self.subfolder.get() else find_file
        matched=sum(1 for row in self.csv_rows
            if fn(folder,(row.get(col_f) or '').strip(),self.match_only.get()))
        total=len(self.csv_rows)
        color=GRN if matched==total else AMB if matched>0 else RED
        self.folder_badge_var.set(f'✓  {matched} of {total} matched')
        self.folder_badge.configure(bg=GRN2 if matched==total else AMB2,
            fg=color,highlightbackground=GRN3 if matched==total else AMB3)
        self.set_status(f'{matched}/{total} files matched',color)

    def open_folder(self):
        f=self.last_folder or self.folder_path.get()
        if f and os.path.exists(f):
            try: os.startfile(f)
            except: pass

    # ── Reset ──────────────────────────────────────────────────────────
    def reset_all(self):
        if self.running:
            messagebox.showwarning('Busy','Wait for current job to finish.'); return
        if not messagebox.askyesno('Reset','Clear everything and start fresh?'): return
        self.csv_path.set(''); self.folder_path.set('')
        self.col_file.set(''); self.col_title.set('')
        self.col_kw.set(''); self.col_desc.set('')
        self.csv_rows=[]; self.csv_headers=[]
        self.csv_badge_var.set('No CSV loaded')
        self.csv_badge.configure(bg=BG3,fg=TXT3,highlightbackground=BDR)
        self.folder_badge_var.set('No folder selected')
        self.folder_badge.configure(bg=BG3,fg=TXT3,highlightbackground=BDR)
        for cb in self.col_combos.values(): cb['values']=[]
        self.sb_prog.configure(value=0)
        self.p_ok.configure(text='0 embedded')
        self.p_warn.configure(text='0 not found')
        self.p_err.configure(text='0 errors')
        self.embed_btn.configure(state='normal',text='▶   Embed Metadata Now')
        self.clear_log()
        self.log('↺  Reset — ready for new batch','info')
        if self.last_summary:
            self.set_status(f'Last: {self.last_summary}',TXT3)
        else:
            self.set_status('',TXT3)

    # ── Embed ──────────────────────────────────────────────────────────
    def start_embed(self):
        if self.running: return
        et=find_exiftool()
        if not et:
            messagebox.showerror('ExifTool not found',
                'Place exiftool.exe next to this app.\nhttps://exiftool.org'); return
        if not self.csv_rows:
            messagebox.showerror('No CSV','Load a CSV first.'); return
        if not self.folder_path.get():
            messagebox.showerror('No folder','Select the image folder.'); return
        fc=self.col_file.get()
        if not fc or fc=='(skip)':
            messagebox.showerror('Column missing','Select the filename column in Step 3.'); return
        self.running=True
        self.embed_btn.configure(state='disabled',text='Processing…')
        threading.Thread(target=self._embed_thread,args=(et,),daemon=True).start()

    def _embed_thread(self,et):
        folder=self.folder_path.get()
        col_f=self.col_file.get(); col_t=self.col_title.get()
        col_k=self.col_kw.get(); col_d=self.col_desc.get()
        use_sub=self.subfolder.get(); use_ext=self.match_only.get()
        rm_prog=self.rm_program.get()
        total=len(self.csv_rows); ok=skipped=errors=0
        finder=find_file_recursive if use_sub else find_file

        self.root.after(0,lambda: self.sb_prog.configure(maximum=total,value=0))
        self.root.after(0,lambda: self.log(f'▶  Batch started — {total} rows','info'))

        for i,row in enumerate(self.csv_rows):
            fn=(row.get(col_f) or '').strip()
            if not fn:
                skipped+=1
                self.root.after(0,lambda n=i+1,t=total,o=ok,s=skipped,e=errors:
                    self._prog(n,t,o,s,e)); continue
            fp=finder(folder,fn,use_ext)
            if not fp:
                skipped+=1
                self.root.after(0,lambda f=fn: self.log(f'⚠  Not found: {f}','warn'))
                self.root.after(0,lambda n=i+1,t=total,o=ok,s=skipped,e=errors:
                    self._prog(n,t,o,s,e)); continue

            cmd=[et,'-overwrite_original','-codedcharacterset=UTF8']
            title=(row.get(col_t) or '').strip() if col_t and col_t!='(skip)' else ''
            kw_raw=(row.get(col_k) or '').strip() if col_k and col_k!='(skip)' else ''
            desc=(row.get(col_d) or '').strip() if col_d and col_d!='(skip)' else ''

            if title: cmd+=[f'-Title={title}',f'-ObjectName={title}',f'-Headline={title}']
            if kw_raw:
                for kw in [k.strip() for k in kw_raw.replace(';',',').split(',') if k.strip()]:
                    cmd+=[f'-Keywords={kw}',f'-Subject={kw}']
            if desc: cmd+=[f'-Description={desc}',f'-Caption-Abstract={desc}']
            if rm_prog: cmd+=['-Software=','-CreatorTool=','-HistorySoftwareAgent=']
            cmd.append(fp)

            try:
                flags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0
                res=subprocess.run(cmd,capture_output=True,text=True,
                    timeout=30,creationflags=flags)
                actual=os.path.basename(fp)
                if res.returncode==0:
                    ok+=1
                    self.root.after(0,lambda fn=actual: self.log(f'✓  {fn}','ok'))
                else:
                    errors+=1
                    err=(res.stderr or res.stdout or 'Unknown').strip()
                    self.root.after(0,lambda fn=actual,e=err:
                        self.log(f'✗  {fn} — {e}','err'))
            except Exception as ex:
                errors+=1
                self.root.after(0,lambda fn=fn,e=str(ex):
                    self.log(f'✗  {fn} — {e}','err'))

            self.root.after(0,lambda n=i+1,t=total,o=ok,s=skipped,e=errors:
                self._prog(n,t,o,s,e))

        summary=f'{ok} embedded · {skipped} not found · {errors} errors'
        self.last_summary=summary
        self.root.after(0,lambda: (
            self.log(f'● Done — {summary}','info'),
            self.set_status(f'Done — {summary}',GRN),
            self.embed_btn.configure(state='normal',text='▶   Embed Metadata Now'),
            setattr(self,'running',False)
        ))

    def _prog(self,n,t,ok,skipped,errors):
        self.sb_prog.configure(value=n)
        self.set_status(f'Processing {n} of {t}…',BLU)
        self.p_ok.configure(text=f'{ok} embedded')
        self.p_warn.configure(text=f'{skipped} not found')
        self.p_err.configure(text=f'{errors} errors')

if __name__=='__main__':
    root=tk.Tk()
    App(root)
    root.mainloop()
