
import customtkinter as ctk
from tkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class MetaZone(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Meta Zone")
        self.geometry("1400x900")
        self.minsize(1100, 700)

        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_main()
        self.build_log()

    def build_header(self):
        top = ctk.CTkFrame(self, corner_radius=0, height=70)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        top.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            top,
            text="Meta Zone",
            font=("Segoe UI", 28, "bold")
        )
        title.grid(row=0, column=0, padx=25, pady=18, sticky="w")

        process_btn = ctk.CTkButton(
            top,
            text="Embed Metadata Now",
            height=42,
            corner_radius=12,
            font=("Segoe UI", 15, "bold")
        )
        process_btn.grid(row=0, column=1, padx=10)

    def card(self, parent, title, number):
        card = ctk.CTkFrame(parent, corner_radius=16)
        card.pack(fill="x", pady=12, padx=10)

        header = ctk.CTkLabel(
            card,
            text=f"{number}   {title}",
            font=("Segoe UI", 18, "bold")
        )
        header.pack(anchor="w", padx=18, pady=(16,10))

        return card

    def build_main(self):
        left = ctk.CTkScrollableFrame(self, corner_radius=0)
        left.grid(row=1, column=0, sticky="nsew", padx=(15,8), pady=15)

        csv_card = self.card(left, "Load CSV", 1)

        row = ctk.CTkFrame(csv_card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0,18))

        entry = ctk.CTkEntry(
            row,
            placeholder_text="Select CSV file...",
            height=42,
            corner_radius=10
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0,10))

        btn = ctk.CTkButton(
            row,
            text="Browse",
            width=130,
            height=42,
            corner_radius=10,
            command=lambda: filedialog.askopenfilename()
        )
        btn.pack(side="right")

        switch = ctk.CTkSwitch(
            csv_card,
            text="Match Filename Only"
        )
        switch.pack(anchor="e", padx=18, pady=(0,18))

        folder_card = self.card(left, "Image Folder", 2)

        row2 = ctk.CTkFrame(folder_card, fg_color="transparent")
        row2.pack(fill="x", padx=18, pady=(0,18))

        entry2 = ctk.CTkEntry(
            row2,
            placeholder_text="Select image folder...",
            height=42,
            corner_radius=10
        )
        entry2.pack(side="left", fill="x", expand=True, padx=(0,10))

        btn2 = ctk.CTkButton(
            row2,
            text="Browse",
            width=130,
            height=42,
            corner_radius=10,
            command=lambda: filedialog.askdirectory()
        )
        btn2.pack(side="right")

        switch2 = ctk.CTkSwitch(
            folder_card,
            text="Include Sub-Folders"
        )
        switch2.pack(anchor="e", padx=18, pady=(0,18))

        map_card = self.card(left, "Map Columns", 3)

        grid = ctk.CTkFrame(map_card, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=18)

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        labels = [
            ("Filename", 0, 0),
            ("Title", 0, 1),
            ("Keywords", 1, 0),
            ("Description", 1, 1)
        ]

        for text, r, c in labels:
            label = ctk.CTkLabel(grid, text=text)
            label.grid(row=r*2, column=c, sticky="w", padx=10, pady=(8,4))

            combo = ctk.CTkComboBox(
                grid,
                values=["Column 1", "Column 2", "Column 3"],
                height=40,
                corner_radius=10
            )
            combo.grid(row=r*2+1, column=c, sticky="ew", padx=10, pady=(0,12))

        remove_switch = ctk.CTkSwitch(
            map_card,
            text="Remove Program Name"
        )
        remove_switch.pack(anchor="e", padx=18, pady=(0,18))

    def build_log(self):
        log = ctk.CTkFrame(self, corner_radius=16)
        log.grid(row=1, column=1, sticky="nsew", padx=(8,15), pady=15)

        title = ctk.CTkLabel(
            log,
            text="Activity Log",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(anchor="w", padx=18, pady=(18,10))

        textbox = ctk.CTkTextbox(
            log,
            corner_radius=10,
            font=("Consolas", 13)
        )
        textbox.pack(fill="both", expand=True, padx=18, pady=(0,18))

        textbox.insert("end", "✓ ExifTool ready\n")
        textbox.insert("end", "✓ Waiting for CSV file...\n")

app = MetaZone()
app.mainloop()
