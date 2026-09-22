from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk, ImageEnhance


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path.home() / "Desktop" / "project"
GENERATOR_PATH = PROJECT_DIR / "generate.py"

BACKGROUND_CANDIDATES = [
    PROJECT_DIR / "music_background.jpg",
    PROJECT_DIR / "music_background.jpeg",
    PROJECT_DIR / "music_background.png",
]


# ============================================================
# COLORS
# ============================================================

BLACK = "#07070D"
WHITE = "#F3F1FA"

MUTED = "#9693A8"
MUTED_2 = "#68667A"

PURPLE = "#7558F2"
PURPLE_HOVER = "#8A72FF"

BLUE = "#4D8CFF"

SUCCESS = "#67CB97"
ERROR = "#E36D7B"

PANEL = "#0B0B14"
PANEL_BORDER = "#27263A"


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_ORDER = 5

MIN_ORDER = 3
MAX_ORDER = 9

BACKGROUND_DARKNESS = 0.38


# ============================================================
# APP
# ============================================================

class MusicGeneratorApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title(
            "Markov Music Generator"
        )

        # ----------------------------------------------------
        # FULLSCREEN
        # ----------------------------------------------------

        self.attributes(
            "-fullscreen",
            True
        )

        self.configure(
            bg=BLACK
        )

        self.bind(
            "<Escape>",
            self.toggle_fullscreen
        )

        # ----------------------------------------------------
        # STATE
        # ----------------------------------------------------

        self.order_value = DEFAULT_ORDER

        self.generation_count = 0

        self.generating = False

        self.process = None

        self.background_source = None
        self.background_photo = None

        self.background_width = 1
        self.background_height = 1

        # ----------------------------------------------------
        # BACKGROUND CANVAS
        # ----------------------------------------------------

        self.canvas = tk.Canvas(
            self,
            bg=BLACK,
            highlightthickness=0,
            bd=0
        )

        self.canvas.pack(
            fill="both",
            expand=True
        )

        self.canvas.bind(
            "<Configure>",
            self.on_resize
        )

        # ----------------------------------------------------
        # FIND IMAGE
        # ----------------------------------------------------

        self.find_background()

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.build_ui()

        self.after(
            50,
            self.refresh_background
        )

    # ========================================================
    # FULLSCREEN
    # ========================================================

    def toggle_fullscreen(
        self,
        event=None
    ):

        current = self.attributes(
            "-fullscreen"
        )

        self.attributes(
            "-fullscreen",
            not current
        )

    # ========================================================
    # FIND BACKGROUND
    # ========================================================

    def find_background(self):

        for path in BACKGROUND_CANDIDATES:

            if path.exists():

                self.background_source = path

                break

    # ========================================================
    # RESIZE
    # ========================================================

    def on_resize(
        self,
        event=None
    ):

        self.background_width = max(
            self.winfo_width(),
            1
        )

        self.background_height = max(
            self.winfo_height(),
            1
        )

        self.refresh_background()
        self.position_ui()

    # ========================================================
    # BACKGROUND
    # ========================================================

    def refresh_background(self):

        width = max(
            self.background_width,
            1
        )

        height = max(
            self.background_height,
            1
        )

        # ----------------------------------------------------
        # No background image
        # ----------------------------------------------------

        if self.background_source is None:

            self.canvas.delete(
                "background"
            )

            self.canvas.configure(
                bg=BLACK
            )

            return

        # ----------------------------------------------------
        # Load image
        # ----------------------------------------------------

        try:

            image = Image.open(
                self.background_source
            ).convert(
                "RGB"
            )

        except Exception:

            self.background_source = None

            self.canvas.delete(
                "background"
            )

            self.canvas.configure(
                bg=BLACK
            )

            return

        # ----------------------------------------------------
        # COVER
        # ----------------------------------------------------

        image_ratio = (
            image.width
            / image.height
        )

        window_ratio = (
            width
            / height
        )

        if image_ratio > window_ratio:

            new_height = height

            new_width = int(
                height
                * image_ratio
            )

        else:

            new_width = width

            new_height = int(
                width
                / image_ratio
            )

        image = image.resize(
            (
                new_width,
                new_height
            ),
            Image.Resampling.LANCZOS
        )

        # ----------------------------------------------------
        # CENTER CROP
        # ----------------------------------------------------

        left = (
            new_width
            - width
        ) // 2

        top = (
            new_height
            - height
        ) // 2

        image = image.crop(
            (
                left,
                top,
                left + width,
                top + height
            )
        )

        # ----------------------------------------------------
        # DARKEN BACKGROUND
        # ----------------------------------------------------

        image = ImageEnhance.Brightness(
            image
        ).enhance(
            BACKGROUND_DARKNESS
        )

        image = ImageEnhance.Contrast(
            image
        ).enhance(
            1.08
        )

        # ----------------------------------------------------
        # Tk image
        # ----------------------------------------------------

        self.background_photo = ImageTk.PhotoImage(
            image
        )

        self.canvas.delete(
            "background"
        )

        self.canvas.create_image(
            width / 2,
            height / 2,
            image=self.background_photo,
            anchor="center",
            tags="background"
        )

        self.canvas.tag_lower(
            "background"
        )

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.brand = self.canvas.create_text(
            0,
            0,
            text="MARKOV",
            fill=WHITE,
            font=(
                "DejaVu Sans",
                32,
                "bold"
            ),
            anchor="center",
            tags="ui"
        )

        self.subtitle = self.canvas.create_text(
            0,
            0,
            text="GENERATIVE MUSIC ENGINE",
            fill=MUTED,
            font=(
                "DejaVu Sans",
                10,
                "bold"
            ),
            anchor="center",
            tags="ui"
        )

        self.description = self.canvas.create_text(
            0,
            0,
            text="Probabilistic music generation",
            fill=MUTED_2,
            font=(
                "DejaVu Sans",
                9
            ),
            anchor="center",
            tags="ui"
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status_dot = self.canvas.create_text(
            0,
            0,
            text="●",
            fill=SUCCESS,
            font=(
                "DejaVu Sans",
                12
            ),
            anchor="center",
            tags="ui"
        )

        self.status_text = self.canvas.create_text(
            0,
            0,
            text="SYSTEM READY",
            fill=MUTED,
            font=(
                "DejaVu Sans",
                9,
                "bold"
            ),
            anchor="center",
            tags="ui"
        )

        # ----------------------------------------------------
        # GENERATE BUTTON
        # ----------------------------------------------------

        self.generate_button = tk.Button(
            self,

            text="♫\nGENERATE MUSIC",

            font=(
                "DejaVu Sans",
                18,
                "bold"
            ),

            bg=PURPLE,
            fg=WHITE,

            activebackground=PURPLE_HOVER,
            activeforeground=WHITE,

            relief="flat",
            bd=0,

            highlightthickness=0,

            cursor="hand2",

            width=18,
            height=3,

            command=self.generate_music
        )

        self.generate_window = (
            self.canvas.create_window(
                0,
                0,
                window=self.generate_button,
                anchor="center",
                tags="ui"
            )
        )

        self.generate_button.bind(
            "<Enter>",
            self.button_enter
        )

        self.generate_button.bind(
            "<Leave>",
            self.button_leave
        )

        # ----------------------------------------------------
        # NOW PLAYING
        # ----------------------------------------------------

        self.now_playing = self.canvas.create_text(
            0,
            0,
            text="",
            fill=WHITE,
            font=(
                "DejaVu Sans",
                10,
                "bold"
            ),
            anchor="center",
            tags="ui"
        )

        # ----------------------------------------------------
        # WAVEFORM
        # ----------------------------------------------------

        self.waveform_canvas = tk.Canvas(
            self,
            width=440,
            height=58,
            bg=BLACK,
            highlightthickness=0,
            bd=0
        )

        self.waveform_window = (
            self.canvas.create_window(
                0,
                0,
                window=self.waveform_canvas,
                anchor="center",
                tags="ui"
            )
        )

        # ----------------------------------------------------
        # ORDER PANEL
        # ----------------------------------------------------

        self.build_order_panel()

        # ----------------------------------------------------
        # BOTTOM INFO
        # ----------------------------------------------------

        self.model_text = self.canvas.create_text(
            0,
            0,
            text=(
                "MODEL  •  MARKOV\n"
                "STATE  •  INTERVAL + RHYTHM"
            ),
            fill="#747186",
            font=(
                "DejaVu Sans",
                8
            ),
            justify="left",
            anchor="sw",
            tags="ui"
        )

        self.counter_text = self.canvas.create_text(
            0,
            0,
            text="GENERATED  00",
            fill="#747186",
            font=(
                "DejaVu Sans",
                8,
                "bold"
            ),
            anchor="se",
            tags="ui"
        )

        # ----------------------------------------------------
        # INITIAL WAVEFORM
        # ----------------------------------------------------

        self.create_waveform(
            active=False
        )

        self.update_order_buttons()

    # ========================================================
    # ORDER PANEL
    # ========================================================

    def build_order_panel(self):

        self.order_frame = tk.Frame(
            self,
            bg=PANEL,
            highlightbackground=PANEL_BORDER,
            highlightthickness=1,
            bd=0
        )

        self.order_window = (
            self.canvas.create_window(
                0,
                0,
                window=self.order_frame,
                anchor="center",
                tags="ui"
            )
        )

        tk.Label(
            self.order_frame,
            text="ORDER",
            bg=PANEL,
            fg=MUTED,
            font=(
                "DejaVu Sans",
                8,
                "bold"
            )
        ).pack(
            side="left",
            padx=(14, 8)
        )

        self.order_buttons = {}

        for value in range(
            MIN_ORDER,
            MAX_ORDER + 1
        ):

            button = tk.Button(
                self.order_frame,
                text=str(value),
                bg=PANEL,
                fg=MUTED,
                activebackground="#211B42",
                activeforeground=WHITE,
                relief="flat",
                bd=0,
                highlightthickness=0,
                width=2,
                height=1,
                cursor="hand2",
                font=(
                    "DejaVu Sans",
                    9,
                    "bold"
                ),
                command=lambda v=value:
                    self.set_order(v)
            )

            button.pack(
                side="left",
                padx=2,
                pady=8
            )

            self.order_buttons[
                value
            ] = button

    # ========================================================
    # ORDER
    # ========================================================

    def set_order(
        self,
        value
    ):

        self.order_value = int(
            max(
                MIN_ORDER,
                min(
                    MAX_ORDER,
                    value
                )
            )
        )

        self.update_order_buttons()

    def update_order_buttons(self):

        for value, button in (
            self.order_buttons.items()
        ):

            if value == self.order_value:

                button.configure(
                    bg=PURPLE,
                    fg=WHITE,
                    activebackground=PURPLE_HOVER,
                    activeforeground=WHITE
                )

            else:

                button.configure(
                    bg=PANEL,
                    fg=MUTED,
                    activebackground="#211B42",
                    activeforeground=WHITE
                )

    # ========================================================
    # POSITION EVERYTHING
    # ========================================================

    def position_ui(self):

        width = max(
            self.winfo_width(),
            800
        )

        height = max(
            self.winfo_height(),
            600
        )

        center_x = width / 2

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        self.canvas.coords(
            self.brand,
            center_x,
            height * 0.105
        )

        self.canvas.coords(
            self.subtitle,
            center_x,
            height * 0.145
        )

        self.canvas.coords(
            self.description,
            center_x,
            height * 0.175
        )

        # ----------------------------------------------------
        # STATUS
        #
        # More space between dot and text.
        # ----------------------------------------------------

        self.canvas.coords(
            self.status_dot,
            center_x - 78,
            height * 0.385
        )

        self.canvas.coords(
            self.status_text,
            center_x + 18,
            height * 0.385
        )

        # ----------------------------------------------------
        # GENERATE BUTTON
        # ----------------------------------------------------

        self.canvas.coords(
            self.generate_window,
            center_x,
            height * 0.50
        )

        # ----------------------------------------------------
        # NOW PLAYING
        # ----------------------------------------------------

        self.canvas.coords(
            self.now_playing,
            center_x,
            height * 0.625
        )

        # ----------------------------------------------------
        # WAVEFORM
        # ----------------------------------------------------

        self.canvas.coords(
            self.waveform_window,
            center_x,
            height * 0.685
        )

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        self.canvas.coords(
            self.order_window,
            center_x,
            height * 0.80
        )

        # ----------------------------------------------------
        # BOTTOM LEFT
        # ----------------------------------------------------

        self.canvas.coords(
            self.model_text,
            38,
            height - 30
        )

        # ----------------------------------------------------
        # BOTTOM RIGHT
        # ----------------------------------------------------

        self.canvas.coords(
            self.counter_text,
            width - 38,
            height - 30
        )

        self.canvas.tag_raise(
            "ui"
        )

    # ========================================================
    # WAVEFORM
    # ========================================================

    def create_waveform(
        self,
        active=False
    ):

        self.waveform_canvas.delete(
            "all"
        )

        bars = [
            8, 14, 10, 20, 30,
            17, 12, 26, 37, 21,
            11, 18, 31, 24, 13,
            18, 28, 16, 10, 17,
            27, 35, 19, 10
        ]

        width = 440
        height = 58

        center_y = height / 2

        spacing = (
            width
            / len(bars)
        )

        for index, value in enumerate(
            bars
        ):

            x = (
                index * spacing
                + spacing / 2
            )

            if active:

                fill = (
                    BLUE
                    if index % 2
                    else PURPLE
                )

            else:

                fill = "#25223C"

            self.waveform_canvas.create_line(
                x,
                center_y - value / 2,
                x,
                center_y + value / 2,
                fill=fill,
                width=3,
                capstyle="round"
            )

    # ========================================================
    # BUTTON HOVER
    # ========================================================

    def button_enter(
        self,
        event
    ):

        if not self.generating:

            self.generate_button.configure(
                bg=PURPLE_HOVER
            )

    def button_leave(
        self,
        event
    ):

        if not self.generating:

            self.generate_button.configure(
                bg=PURPLE
            )

    # ========================================================
    # GENERATE
    # ========================================================

    def generate_music(self):

        if self.generating:
            return

        # ----------------------------------------------------
        # Check generator
        # ----------------------------------------------------

        if not GENERATOR_PATH.exists():

            messagebox.showerror(
                "Generator Error",
                (
                    "generate.py پیدا نشد.\n\n"
                    f"{GENERATOR_PATH}"
                )
            )

            return

        # ----------------------------------------------------
        # Find project Python
        # ----------------------------------------------------

        python_path = (
            PROJECT_DIR
            / ".venv"
            / "bin"
            / "python"
        )

        if not python_path.exists():

            python_path = Path(
                sys.executable
            )

        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        self.generating = True

        self.generate_button.configure(
            state="disabled",
            bg="#393266",
            cursor="arrow"
        )

        self.canvas.itemconfigure(
            self.status_dot,
            fill=PURPLE
        )

        self.canvas.itemconfigure(
            self.status_text,
            text="GENERATING..."
        )

        self.canvas.itemconfigure(
            self.now_playing,
            text=""
        )

        self.create_waveform(
            active=True
        )

        # ----------------------------------------------------
        # Run generator
        #
        # generate.py:
        #
        # python generate.py ORDER
        # ----------------------------------------------------

        args = [
            str(python_path),
            str(GENERATOR_PATH),
            str(self.order_value)
        ]

        try:

            self.process = subprocess.Popen(
                args,
                cwd=str(PROJECT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

        except Exception as exc:

            self.finish_generation(
                False,
                f"Could not start generator:\n{exc}"
            )

            return

        self.after(
            250,
            self.check_process
        )

    # ========================================================
    # PROCESS CHECK
    # ========================================================

    def check_process(self):

        if self.process is None:
            return

        code = self.process.poll()

        if code is None:

            self.after(
                250,
                self.check_process
            )

            return

        output = ""

        try:

            if self.process.stdout:

                output = (
                    self.process.stdout
                    .read()
                    .strip()
                )

        except Exception:

            output = ""

        self.finish_generation(
            code == 0,
            output
        )

    # ========================================================
    # FINISH
    # ========================================================

    def finish_generation(
        self,
        success,
        output=""
    ):

        self.generating = False

        self.generate_button.configure(
            state="normal",
            bg=PURPLE,
            cursor="hand2"
        )

        if success:

            self.generation_count += 1

            self.canvas.itemconfigure(
                self.status_dot,
                fill=SUCCESS
            )

            self.canvas.itemconfigure(
                self.status_text,
                text="MUSIC GENERATED"
            )

            self.canvas.itemconfigure(
                self.now_playing,
                text=(
                    "♫  NOW PLAYING  •  "
                    "generated_music.mid"
                )
            )

            self.canvas.itemconfigure(
                self.counter_text,
                text=(
                    "GENERATED  "
                    f"{self.generation_count:02d}"
                )
            )

            self.create_waveform(
                active=True
            )

        else:

            self.canvas.itemconfigure(
                self.status_dot,
                fill=ERROR
            )

            self.canvas.itemconfigure(
                self.status_text,
                text="GENERATION ERROR"
            )

            self.create_waveform(
                active=False
            )

            if output:

                messagebox.showerror(
                    "Generation Error",
                    output[-7000:]
                )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app = MusicGeneratorApp()

    app.mainloop()

