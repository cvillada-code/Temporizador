import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk, ImageDraw
import pygame
import math

# ── Paleta de colores ──────────────────────────────────────────────────────────
BG          = "#0f0f1a"   # fondo principal
PANEL       = "#1a1a2e"   # panel / canvas
RING_BG     = "#2a2a3e"   # aro base (gris azulado)
RING_FG     = "#00e5a0"   # progreso (verde menta)
RING_ALERT  = "#ff4d6d"   # alerta / tiempo restante en rojo
TEXT_MAIN   = "#e8e8f0"   # texto principal
TEXT_DIM    = "#6b6b8a"   # texto secundario
BTN_START   = "#00e5a0"   # botón iniciar
BTN_START_H = "#00c988"   # hover botón iniciar
BTN_RESET   = "#2a2a3e"   # botón reiniciar
BTN_RESET_H = "#3a3a5e"   # hover botón reiniciar
ENTRY_BG    = "#1a1a2e"
ENTRY_FG    = "#e8e8f0"
ENTRY_BORDER= "#3a3a5e"
# ──────────────────────────────────────────────────────────────────────────────

# ====Versión
VERSION = "v.24"

CANVAS_SIZE  = 380
CX = CY      = CANVAS_SIZE // 2   # centro
RADIO        = 140
LINE_W       = 14

# ── Nivel de transparencia ─────────────────────────────────────────────────────
ALPHA        = 0.88   # 0.0 = invisible · 1.0 = sólido
# ──────────────────────────────────────────────────────────────────────────────


def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def interpolate_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


class Temporizador:
    def __init__(self, root):
        self.root = root
        #self.root.title("Temporizador")
        self.root.title(f"Temporizador_{VERSION}") 
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # ── Transparencia ──────────────────────────────────────────────────────
        self.root.attributes('-alpha', ALPHA)
        # En Windows puedes usar además:
        # self.root.attributes('-transparentcolor', BG)  # hace BG 100% transparente
        # ──────────────────────────────────────────────────────────────────────

        self.tiempo_restante  = 0
        self.total_tiempo     = 1
        self.audio_habilitado = False
        self._hover_start     = False
        self._hover_reset     = False

        pygame.mixer.init()

        self._build_ui()
        self._dibujar_borde_inicial()

    # ── Construcción de la UI ──────────────────────────────────────────────────

    def _build_ui(self):
        # Canvas circular
        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_SIZE, height=CANVAS_SIZE,
            bg=PANEL, highlightthickness=0
        )
        self.canvas.pack(padx=24, pady=(24, 0))

        # ── Zona de entrada ────────────────────────────────────────────────────
        input_frame = tk.Frame(self.root, bg=BG)
        input_frame.pack(pady=(16, 0), padx=24)

        lbl = tk.Label(
            input_frame, text="hh  :  mm  :  ss",
            font=("Helvetica", 9, "bold"), fg=TEXT_DIM, bg=BG
        )
        lbl.pack()

        # Entry con borde simulado mediante frame
        entry_wrapper = tk.Frame(input_frame, bg=ENTRY_BORDER, bd=0)
        entry_wrapper.pack(pady=(6, 0))

        self.tiempo_entry = tk.Entry(
            entry_wrapper,
            justify="center",
            font=("Helvetica", 18, "bold"),
            width=10,
            bg=ENTRY_BG, fg=ENTRY_FG,
            insertbackground=ENTRY_FG,
            relief="flat",
            bd=8
        )
        self.tiempo_entry.pack(padx=2, pady=2)
        self.tiempo_entry.insert(0, "00:00:00")
        self.tiempo_entry.bind("<FocusIn>",  self._entry_focus_in)
        self.tiempo_entry.bind("<FocusOut>", self._entry_focus_out)

        # ── Botones ────────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(pady=(16, 24))

        # Botón Iniciar
        self.btn_start = tk.Label(
            btn_frame,
            text="▶  Iniciar",
            font=("Helvetica", 12, "bold"),
            bg=BTN_START, fg="#0f0f1a",
            padx=24, pady=10,
            cursor="hand2"
        )
        self.btn_start.grid(row=0, column=0, padx=(0, 10))
        self.btn_start.bind("<Button-1>", lambda e: self.iniciar_temporizador())
        self.btn_start.bind("<Enter>",    lambda e: self.btn_start.config(bg=BTN_START_H))
        self.btn_start.bind("<Leave>",    lambda e: self.btn_start.config(bg=BTN_START))

        # Botón Reiniciar
        self.btn_reset = tk.Label(
            btn_frame,
            text="↺  Reiniciar",
            font=("Helvetica", 12, "bold"),
            bg=BTN_RESET, fg=TEXT_MAIN,
            padx=24, pady=10,
            cursor="hand2"
        )
        self.btn_reset.grid(row=0, column=1)
        self.btn_reset.bind("<Button-1>", lambda e: self.reiniciar_temporizador())
        self.btn_reset.bind("<Enter>",    lambda e: self.btn_reset.config(bg=BTN_RESET_H))
        self.btn_reset.bind("<Leave>",    lambda e: self.btn_reset.config(bg=BTN_RESET))

        for btn in (self.btn_start, self.btn_reset):
            btn.config(relief="flat")

    # ── Dibujo ─────────────────────────────────────────────────────────────────

    def _dibujar_borde_inicial(self):
        self.canvas.delete("all")
        self._draw_background_decoration()
        self._draw_ring(BG_ring=RING_BG, FG_ring=None, porcentaje=0)
        self._draw_center_text("00:00:00", dim=True)

    def _draw_background_decoration(self):
        """Círculos concéntricos tenues de fondo."""
        for i, r in enumerate([RADIO + 40, RADIO + 70, RADIO + 95]):
            alpha = 30 - i * 8
            color = interpolate_color(PANEL, RING_BG, alpha / 100)
            self.canvas.create_oval(
                CX - r, CY - r, CX + r, CY + r,
                outline=color, width=1
            )

    def _draw_ring(self, BG_ring, FG_ring, porcentaje):
        pad = 7
        self.canvas.create_oval(
            CX - RADIO - pad, CY - RADIO - pad,
            CX + RADIO + pad, CY + RADIO + pad,
            outline=BG_ring, width=LINE_W
        )

        if FG_ring and porcentaje > 0:
            extent = -360 * porcentaje

            if porcentaje < 0.5:
                color = interpolate_color(RING_FG, "#ffbe00", porcentaje * 2)
            else:
                color = interpolate_color("#ffbe00", RING_ALERT, (porcentaje - 0.5) * 2)

            self.canvas.create_arc(
                CX - RADIO - pad, CY - RADIO - pad,
                CX + RADIO + pad, CY + RADIO + pad,
                start=90, extent=extent,
                style=tk.ARC, outline=color, width=LINE_W
            )

            # Punto brillante en el extremo del arco
            angle_rad = math.radians(90 + extent)
            tip_x = CX + (RADIO + pad) * math.cos(angle_rad)
            tip_y = CY - (RADIO + pad) * math.sin(angle_rad)
            dot_r = LINE_W // 2 + 1
            self.canvas.create_oval(
                tip_x - dot_r, tip_y - dot_r,
                tip_x + dot_r, tip_y + dot_r,
                fill=color, outline=""
            )

    def _draw_center_text(self, tiempo_str, dim=False):
        color = TEXT_DIM if dim else TEXT_MAIN

        self.canvas.create_text(
            CX, CY - 10,
            text=tiempo_str,
            font=("Courier", 28, "bold"),
            fill=color
        )
        self.canvas.create_text(
            CX, CY + 28,
            text="TIEMPO RESTANTE",
            font=("Helvetica", 7, "bold"),
            fill=TEXT_DIM
        )

    # ── Lógica del temporizador ────────────────────────────────────────────────

    def iniciar_temporizador(self):
        tiempo_str = self.tiempo_entry.get()
        try:
            h, m, s = map(int, tiempo_str.split(':'))
            self.total_tiempo    = h * 3600 + m * 60 + s
            self.tiempo_restante = self.total_tiempo
            if self.total_tiempo == 0:
                return
            self.audio_habilitado = True
            self._dibujar_progreso()
            self._actualizar_temporizador()
        except ValueError:
            self._shake_entry()

    def _actualizar_temporizador(self):
        if self.tiempo_restante > 0:
            self.tiempo_restante -= 1
            self._dibujar_progreso()
            self.root.after(1000, self._actualizar_temporizador)
        else:
            self._accion_final()

    def _dibujar_progreso(self):
        self.canvas.delete("all")
        self._draw_background_decoration()

        porcentaje = (
            (self.total_tiempo - self.tiempo_restante) / self.total_tiempo
            if self.total_tiempo > 0 else 0
        )
        self._draw_ring(BG_ring=RING_BG, FG_ring=RING_FG, porcentaje=porcentaje)

        tiempo_str = self._convertir_a_hh_mm_ss(self.tiempo_restante)

        color = RING_ALERT if self.tiempo_restante <= 10 else TEXT_MAIN
        self.canvas.create_text(
            CX, CY - 10,
            text=tiempo_str,
            font=("Courier", 28, "bold"),
            fill=color
        )
        self.canvas.create_text(
            CX, CY + 28,
            text="TIEMPO RESTANTE",
            font=("Helvetica", 7, "bold"),
            fill=TEXT_DIM
        )

        pct_text = f"{int(porcentaje * 100)}%"
        self.canvas.create_text(
            CX, CY + 54,
            text=pct_text,
            font=("Helvetica", 9),
            fill=TEXT_DIM
        )

    def _accion_final(self):
        if self.audio_habilitado:
            self._reproducir_audio()
        self._maximizar_y_traer_al_frente()
        self._animacion_alerta()

    def _maximizar_y_traer_al_frente(self):
        self.root.deiconify()
        self.root.state("normal")
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()
        self.root.after(1000, lambda: self.root.attributes("-topmost", False))

    def _animacion_alerta(self, count=6):
        if count > 0:
            nuevo_color = RING_ALERT if self.canvas["bg"] == PANEL else PANEL
            self.canvas.config(bg=nuevo_color)
            self.root.after(300, self._animacion_alerta, count - 1)
        else:
            self.canvas.config(bg=PANEL)
            self._vibracion_ventana()

    def _vibracion_ventana(self, count=20):
        if count > 0:
            x, y = self.root.winfo_x(), self.root.winfo_y()
            d = 8 if count % 2 == 0 else -8
            self.root.geometry(f"+{x + d}+{y}")
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.focus_force()
            self.root.after(50, self._vibracion_ventana, count - 1)
        else:
            self.root.attributes("-topmost", False)

    def reiniciar_temporizador(self, event=None):
        self.tiempo_restante  = 0
        self.audio_habilitado = False
        self.tiempo_entry.delete(0, tk.END)
        self.tiempo_entry.insert(0, "00:00:00")
        self._dibujar_borde_inicial()

    def _shake_entry(self, count=6):
        """Sacude el campo de entrada si el formato es inválido."""
        if count > 0:
            self.root.after(40, self._shake_entry, count - 1)

    def _reproducir_audio(self):
        try:
            pygame.mixer.music.load("audio.mp3")
            pygame.mixer.music.play()
        except Exception:
            pass

    def _entry_focus_in(self, event):
        if self.tiempo_entry.get() == "00:00:00":
            self.tiempo_entry.delete(0, tk.END)

    def _entry_focus_out(self, event):
        if not self.tiempo_entry.get():
            self.tiempo_entry.insert(0, "00:00:00")

    # ── Utilidades ─────────────────────────────────────────────────────────────

    @staticmethod
    def _convertir_a_hh_mm_ss(tiempo):
        h = tiempo // 3600
        m = (tiempo % 3600) // 60
        s = tiempo % 60
        return f"{h:02}:{m:02}:{s:02}"


if __name__ == "__main__":
    root = tk.Tk()
    app  = Temporizador(root)
    root.mainloop()