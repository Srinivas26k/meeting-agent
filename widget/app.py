"""
Meeting Agent — Floating Widget
Dark pill-card aesthetic. Always-on-top overlay for recording and processing.
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import platform
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# ── palette (matches reference design) ────────────────────────────────────────
BG_APP      = "#E8E8E8"   # light grey app background
BG_CARD     = "#111111"   # near-black card
BG_CARD2    = "#1A1A1A"   # slightly lighter card
BG_PILL     = "#222222"   # inner pill background
ACCENT      = "#00FF88"   # green accent
ACCENT_DIM  = "#00CC66"   # darker green
RED         = "#FF4444"
AMBER       = "#FFB800"
TEXT_PRI    = "#FFFFFF"
TEXT_SEC    = "#888888"
TEXT_DIM    = "#555555"
BORDER      = "#2A2A2A"


class AnimatedDot(tk.Canvas):
    """Pulsing recording indicator."""
    def __init__(self, parent, **kw):
        super().__init__(parent, width=10, height=10,
                         bg=BG_CARD, highlightthickness=0, **kw)
        self._dot = self.create_oval(1, 1, 9, 9, fill=RED, outline="")
        self._phase = 0
        self._anim_id = None

    def start(self):
        self._animate()

    def stop(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self.itemconfig(self._dot, fill=TEXT_DIM)

    def _animate(self):
        self._phase = (self._phase + 0.15) % (2 * 3.14159)
        import math
        alpha = int(155 + 100 * math.sin(self._phase))
        r = alpha; g = 0; b = 0
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.itemconfig(self._dot, fill=color)
        self._anim_id = self.after(60, self._animate)


class PillButton(tk.Button):
    """Pill-styled button — uses tk.Button for reliable cross-platform geometry."""
    def __init__(self, parent, text, command, color=ACCENT,
                 text_color="#000000", width=90, small=False, **kw):
        font_size = 9 if small else 10
        # Convert pixel width to approximate character width
        char_width = max(8, width // 8)
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=text_color,
            activebackground=PillButton._darken(color),
            activeforeground=text_color,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("SF Pro Display", font_size, "bold"),
            width=char_width,
            pady=6 if small else 8,
        )
        self._color = color
        self._text_color = text_color

    @staticmethod
    def _darken(hex_color):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{max(0,r-30):02x}{max(0,g-30):02x}{max(0,b-30):02x}"

    def update_text(self, text):
        self.config(text=text)

    def update_color(self, color, text_color="#000000"):
        self._color = color
        self._text_color = text_color
        self.config(
            bg=color,
            fg=text_color,
            activebackground=self._darken(color),
            activeforeground=text_color,
        )


class IconButton(tk.Label):
    """Small circular icon button — uses tk.Label for reliable cross-platform geometry."""
    def __init__(self, parent, symbol, command, size=32,
                 bg=BG_PILL, fg=TEXT_SEC, **kw):
        kw.pop("width", None)
        kw.pop("height", None)
        super().__init__(
            parent,
            text=symbol,
            fg=fg,
            bg=bg,
            font=("SF Pro Display", 12),
            cursor="hand2",
            padx=4, pady=4,
            **kw,
        )
        self._bg = bg
        self.bind("<Enter>",    lambda e: self.config(bg=BORDER))
        self.bind("<Leave>",    lambda e: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda e: command())


class StatusPill(tk.Label):
    """Small status pill label."""
    def __init__(self, parent, text, color=ACCENT, **kw):
        super().__init__(
            parent, text=f"● {text}",
            fg=color, bg=BG_CARD,
            font=("SF Pro Display", 9, "bold"),
            padx=6, pady=2,
        )

    def update(self, text):
        self.config(text=f"● {text}")


class MeetingWidget:
    """Floating always-on-top meeting recorder — dark pill-card aesthetic."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Meeting Agent")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_APP)
        self.root.attributes("-topmost", True)
        if platform.system() in ("Windows", "Darwin"):
            self.root.attributes("-alpha", 0.97)
        self.root.overrideredirect(True)

        # state
        self.recording    = False
        self.mode         = tk.StringVar(value="screen")
        self.recorder     = None
        self._timer_id    = None
        self.output_path  = None
        self.intelligence = None
        self._transcript_text_cache = None
        self._drag_x = self._drag_y = 0
        self._current_view = "main"   # main | transcript | result

        self._build_ui()
        self._position_top_right()
        self._bind_drag()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _card(self, parent, pad_x=14, pad_y=10, bg=BG_CARD):
        """Return a rounded-looking frame (canvas-backed card)."""
        f = tk.Frame(parent, bg=bg, padx=pad_x, pady=pad_y)
        return f

    def _build_ui(self):
        # ── outer wrapper ──
        outer = tk.Frame(self.root, bg=BG_APP, padx=10, pady=10)
        outer.pack(fill="both", expand=True)

        # ── title bar card ──
        title_card = tk.Frame(outer, bg=BG_CARD,
                               padx=14, pady=10)
        title_card.pack(fill="x", pady=(0, 6))
        self._round_frame(title_card)

        title_row = tk.Frame(title_card, bg=BG_CARD)
        title_row.pack(fill="x")

        # logo dot
        dot = tk.Canvas(title_row, width=10, height=10,
                        bg=BG_CARD, highlightthickness=0)
        dot.create_oval(0, 0, 10, 10, fill=ACCENT, outline="")
        dot.pack(side="left", padx=(0, 6))

        tk.Label(title_row, text="Meeting Agent",
                 fg=TEXT_PRI, bg=BG_CARD,
                 font=("SF Pro Display", 12, "bold")).pack(side="left")

        # window controls (right side)
        ctrl = tk.Frame(title_row, bg=BG_CARD)
        ctrl.pack(side="right")

        for sym, cmd, col in [("−", self._minimise, TEXT_DIM),
                               ("✕", self._on_close, TEXT_DIM)]:
            b = tk.Label(ctrl, text=sym, fg=col, bg=BG_CARD,
                         font=("SF Pro Display", 13), cursor="hand2",
                         padx=4)
            b.pack(side="left")
            b.bind("<Button-1>", lambda e, c=cmd: c())

        # ── mode selector card ──
        mode_card = tk.Frame(outer, bg=BG_CARD, padx=14, pady=8)
        mode_card.pack(fill="x", pady=(0, 6))

        mode_lbl = tk.Label(mode_card, text="MODE",
                            fg=TEXT_DIM, bg=BG_CARD,
                            font=("SF Pro Display", 9, "bold"))
        mode_lbl.pack(anchor="w")

        btns = tk.Frame(mode_card, bg=BG_CARD)
        btns.pack(fill="x", pady=(6, 0))

        self._mode_btns = {}
        modes = [("⬛  Screen", "screen"), ("🎤  Mic", "mic"),
                 ("🔊  System", "system")]
        for label, val in modes:
            b = tk.Label(btns, text=label,
                         fg=TEXT_SEC, bg=BG_PILL,
                         font=("SF Pro Display", 9),
                         padx=10, pady=4, cursor="hand2")
            b.pack(side="left", padx=(0, 4))
            b.bind("<Button-1>", lambda e, v=val: self._set_mode(v))
            self._mode_btns[val] = b
        self._set_mode("screen")

        # ── timer card (the big display card) ──
        self.timer_card = tk.Frame(outer, bg=BG_CARD, padx=14, pady=14)
        self.timer_card.pack(fill="x", pady=(0, 6))

        t_top = tk.Frame(self.timer_card, bg=BG_CARD)
        t_top.pack(fill="x")

        self._rec_dot = AnimatedDot(t_top)
        self._rec_dot.pack(side="left", padx=(0, 6))
        self.status_lbl = tk.Label(t_top, text="Ready",
                                   fg=TEXT_SEC, bg=BG_CARD,
                                   font=("SF Pro Display", 9))
        self.status_lbl.pack(side="left")

        self._updated_lbl = tk.Label(t_top, text="",
                                     fg=TEXT_DIM, bg=BG_CARD,
                                     font=("SF Pro Display", 9))
        self._updated_lbl.pack(side="right")

        self.timer_lbl = tk.Label(self.timer_card,
                                  text="00:00",
                                  fg=TEXT_PRI, bg=BG_CARD,
                                  font=("SF Pro Display", 32, "bold"))
        self.timer_lbl.pack(anchor="w", pady=(4, 0))

        self.sub_lbl = tk.Label(self.timer_card,
                                text="Press record to start",
                                fg=TEXT_DIM, bg=BG_CARD,
                                font=("SF Pro Display", 10))
        self.sub_lbl.pack(anchor="w")

        # ── action row ──
        act_card = tk.Frame(outer, bg=BG_CARD, padx=14, pady=10)
        act_card.pack(fill="x", pady=(0, 6))

        act_row = tk.Frame(act_card, bg=BG_CARD)
        act_row.pack(fill="x")

        self.rec_btn = PillButton(act_row, "⏺  Record",
                                   self._toggle_recording,
                                   color=ACCENT, width=110)
        self.rec_btn.pack(side="left")

        btns_right = tk.Frame(act_card, bg=BG_CARD)
        btns_right.pack(fill="x", pady=(8, 0))

        self.process_btn = PillButton(btns_right, "⚡  Process",
                                       self._process_recording,
                                       color=BG_PILL,
                                       text_color=TEXT_SEC, width=110)
        self.process_btn.pack(side="left", padx=(0, 6))

        self.transcript_btn = PillButton(btns_right, "📄  Transcript",
                                          self._show_transcript,
                                          color=BG_PILL,
                                          text_color=TEXT_SEC, width=110)
        self.transcript_btn.pack(side="left")
        # ── result card (hidden initially) ──
        self.result_card = tk.Frame(outer, bg=BG_CARD, padx=14, pady=10)

        r_header = tk.Frame(self.result_card, bg=BG_CARD)
        r_header.pack(fill="x", pady=(0, 8))

        self.result_title = tk.Label(r_header, text="",
                                     fg=TEXT_PRI, bg=BG_CARD,
                                     font=("SF Pro Display", 11, "bold"),
                                     wraplength=220, justify="left")
        self.result_title.pack(side="left", fill="x", expand=True)

        self._result_status = StatusPill(r_header, "done", ACCENT)
        self._result_status.pack(side="right")

        self.result_body = tk.Label(self.result_card, text="",
                                    fg=TEXT_SEC, bg=BG_CARD,
                                    font=("SF Pro Display", 10),
                                    wraplength=220, justify="left")
        self.result_body.pack(anchor="w", pady=(0, 10))

        # action item count pill row
        self._pill_row = tk.Frame(self.result_card, bg=BG_CARD)
        self._pill_row.pack(fill="x", pady=(0, 8))

        self._items_pill  = StatusPill(self._pill_row, "0 actions", ACCENT)
        self._items_pill.pack(side="left", padx=(0, 6))
        self._dec_pill    = StatusPill(self._pill_row, "0 decisions", AMBER)
        self._dec_pill.pack(side="left")

        # delivery buttons row
        delivery_row = tk.Frame(self.result_card, bg=BG_CARD)
        delivery_row.pack(fill="x")

        PillButton(delivery_row, "✉  Send Email",
                   self._send_email,
                   color=ACCENT, width=110).pack(side="left", padx=(0, 6))

        PillButton(delivery_row, "📋  Copy Notes",
                   self._copy_notes,
                   color=BG_PILL, text_color=TEXT_SEC, width=110).pack(side="left")

        # ── transcript view card (hidden initially) ──
        self.transcript_card = tk.Frame(outer, bg=BG_CARD, padx=14, pady=10)

        tx_header = tk.Frame(self.transcript_card, bg=BG_CARD)
        tx_header.pack(fill="x", pady=(0, 8))

        tk.Label(tx_header, text="TRANSCRIPT",
                 fg=TEXT_DIM, bg=BG_CARD,
                 font=("SF Pro Display", 9, "bold")).pack(side="left")

        close_tx = tk.Label(tx_header, text="✕",
                            fg=TEXT_DIM, bg=BG_CARD,
                            font=("SF Pro Display", 11), cursor="hand2")
        close_tx.pack(side="right")
        close_tx.bind("<Button-1>", lambda e: self._hide_transcript())

        self.transcript_text = scrolledtext.ScrolledText(
            self.transcript_card,
            bg=BG_PILL, fg=TEXT_SEC,
            font=("SF Pro Display", 9),
            relief="flat", bd=0,
            width=28, height=8,
            wrap="word",
            state="disabled",
            insertbackground=ACCENT)
        self.transcript_text.pack(fill="both", expand=True)

        # style the scrollbar
        style = ttk.Style()
        style.configure("Vertical.TScrollbar",
                        background=BG_CARD, troughcolor=BG_PILL,
                        bordercolor=BG_CARD, arrowcolor=TEXT_DIM)

        # ── progress bar (hidden until processing) ──
        self.progress_card = tk.Frame(outer, bg=BG_CARD, padx=14, pady=10)
        self._prog_lbl = tk.Label(self.progress_card,
                                  text="Processing...",
                                  fg=TEXT_SEC, bg=BG_CARD,
                                  font=("SF Pro Display", 10))
        self._prog_lbl.pack(anchor="w", pady=(0, 6))

        self._prog_bar = tk.Canvas(self.progress_card, height=3,
                                   bg=BG_PILL, highlightthickness=0)
        self._prog_bar.pack(fill="x")
        self._prog_fill = self._prog_bar.create_rectangle(
            0, 0, 0, 3, fill=ACCENT, outline="")
        self._prog_width = 0
        self._prog_anim_id = None

    def _round_frame(self, frame):
        """Visual trick: give frame a slight inset by using a border canvas."""
        pass  # tkinter doesn't support CSS border-radius; keep clean

    # ── mode ──────────────────────────────────────────────────────────────────

    def _set_mode(self, val):
        self.mode.set(val)
        for v, b in self._mode_btns.items():
            if v == val:
                b.config(fg=TEXT_PRI, bg=ACCENT,
                         font=("SF Pro Display", 9, "bold"))
            else:
                b.config(fg=TEXT_SEC, bg=BG_PILL,
                         font=("SF Pro Display", 9))

    # ── drag ──────────────────────────────────────────────────────────────────

    def _bind_drag(self):
        self.root.bind("<ButtonPress-1>",  self._drag_start)
        self.root.bind("<B1-Motion>",      self._drag_move)

    def _drag_start(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _position_top_right(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        w  = self.root.winfo_width()
        self.root.geometry(f"+{sw - w - 20}+40")

    # ── recording ─────────────────────────────────────────────────────────────

    def _toggle_recording(self):
        if self.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        mode = self.mode.get()
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.timer_lbl.config(text="00:00")
        try:
            if mode == "screen":
                from capture.screen_recorder import ScreenRecorder
                self.recorder   = ScreenRecorder()
                self.output_path = self.recorder.start(f"recording_screen_{ts}.mp4")
            elif mode == "mic":
                from capture.mic_recorder import MicRecorder
                self.recorder   = MicRecorder()
                self.recorder.start()
                self.output_path = Path(f"recording_mic_{ts}.wav")
            elif mode == "system":
                from capture.system_audio import SystemAudioRecorder
                self.recorder   = SystemAudioRecorder()
                self.recorder.start()
                self.output_path = Path(f"recording_system_{ts}.wav")
        except Exception as ex:
            err_msg = str(ex)
            if len(err_msg) > 150:
                err_msg = err_msg[:150] + "...\n(Check terminal for full error)"
            messagebox.showerror("Recording Error", err_msg)
            return

        self.recording = True
        self.rec_btn.update_text("⏹  Stop")
        self.rec_btn.update_color(RED, TEXT_PRI)
        self._rec_dot.start()
        self._set_status(f"Recording · {mode}", RED)
        self.sub_lbl.config(text="Recording in progress…")
        self._updated_lbl.config(text="live")

        self.recording_start_time = time.time()
        self._update_timer_loop()

    def _update_timer_loop(self):
        if not self.recording:
            return
        elapsed = int(time.time() - self.recording_start_time)
        m, s = divmod(elapsed, 60)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self._timer_id = self.root.after(1000, self._update_timer_loop)

    def _stop_recording(self):
        self.recording = False
        if getattr(self, '_timer_id', None):
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._rec_dot.stop()
        try:
            if self.mode.get() == "screen":
                self.output_path = self.recorder.stop()
            else:
                self.output_path = self.recorder.stop(str(self.output_path))
        except Exception as ex:
            self._set_status(f"Stop error: {ex}", AMBER)

        self.rec_btn.update_text("⏺  Record")
        self.rec_btn.update_color(ACCENT)
        self._set_status("Saved", ACCENT)
        if self.output_path:
            out_path = Path(self.output_path)
            self.sub_lbl.config(text=f"Saved: {out_path.name} · {out_path.parent}")
        else:
            self.sub_lbl.config(text="Stopped")
        self._updated_lbl.config(text="just now")

    # ── processing ────────────────────────────────────────────────────────────

    def _process_recording(self):
        if not self.output_path or not Path(self.output_path).exists():
            messagebox.showwarning("No recording", "Record something first.")
            return
        self._hide_transcript()
        self._show_progress()
        self._start_progress_anim()
        threading.Thread(target=self._run_pipeline, daemon=True).start()

    def _run_pipeline(self):
        try:
            from capture.file_loader import FileLoader
            from processing.preprocessor import AudioPreprocessor
            from processing.transcriber import Transcriber
            from intelligence.pipeline import IntelligencePipeline
            from storage.database import Database

            self._set_prog("Loading file…")
            path = FileLoader.load(str(self.output_path))

            self._set_prog("Preprocessing audio…")
            audio = AudioPreprocessor().process(path)

            self._set_prog("Transcribing…")
            transcript = Transcriber().transcribe(audio)
            self._transcript_text_cache = transcript.get('text', '')

            self._set_prog("Extracting intelligence…")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                intel = loop.run_until_complete(
                    IntelligencePipeline().process(transcript['text']))
                loop.close()
            except Exception as exc:
                self.root.after(0, lambda: self._show_transcript_after_processing(
                    f"Transcript ready (intelligence unavailable: {exc})"
                ))
                return

            self.intelligence = intel
            self._transcript_text_cache = transcript['text']

            db = Database()
            db.create_meeting({
                'title':            intel.summary.title,
                'participants':     intel.summary.participants,
                'duration_minutes': intel.summary.duration_minutes,
                'audio_file_path':  str(self.output_path),
                'transcript':       intel.transcript,
                'summary':          intel.summary.summary,
                'key_points':       intel.summary.key_points,
                'action_items':     [i.model_dump() for i in intel.action_items],
                'decisions':        [d.model_dump() for d in intel.decisions],
            })

            # cleanup temp file
            try:
                processed = path.parent / f"{path.stem}_processed.wav"
                processed.unlink(missing_ok=True)
            except Exception:
                pass

            self.root.after(0, lambda: self._show_result(intel))

        except Exception as ex:
            self.root.after(0, lambda: self._show_error(str(ex)))

    def _show_result(self, intel):
        self._stop_progress_anim()
        self.progress_card.pack_forget()

        self.result_title.config(text=intel.summary.title)
        summary_short = intel.summary.summary[:120]
        if len(intel.summary.summary) > 120:
            summary_short += "…"
        self.result_body.config(text=summary_short)
        self._items_pill.update(f"{len(intel.action_items)} actions")
        self._dec_pill.update(f"{len(intel.decisions)} decisions")
        self.result_card.pack(fill="x", pady=(0, 6))
        self._set_status("Done", ACCENT)
        self.sub_lbl.config(text="Processing complete")

    def _show_transcript_after_processing(self, status_msg: str):
        self._stop_progress_anim()
        self.progress_card.pack_forget()
        self._set_status("Transcript ready", ACCENT)
        self.sub_lbl.config(text=status_msg)
        self._show_transcript()

    def _show_error(self, msg):
        self._stop_progress_anim()
        self.progress_card.pack_forget()
        self._set_status(f"Error", RED)
        err_msg = str(msg)
        if len(err_msg) > 150:
            err_msg = err_msg[:150] + "...\n(Check terminal for full error)"
        messagebox.showerror("Processing failed", err_msg)

    # ── transcript view ───────────────────────────────────────────────────────

    def _show_transcript(self):
        text = getattr(self, '_transcript_text_cache', None)
        if not text:
            if self.intelligence:
                text = self.intelligence.transcript
            else:
                messagebox.showinfo("No transcript",
                                    "Process a recording first to see transcript.")
                return
        self.transcript_text.config(state="normal")
        self.transcript_text.delete("1.0", "end")
        self.transcript_text.insert("end", text)
        self.transcript_text.config(state="disabled")
        self.transcript_card.pack(fill="x", pady=(0, 6))

    def _hide_transcript(self):
        self.transcript_card.pack_forget()

    # ── email + copy ──────────────────────────────────────────────────────────

    def _send_email(self):
        if not self.intelligence:
            messagebox.showwarning("No data", "Process a recording first.")
            return
        # open a small email dialog
        self._open_email_dialog()

    def _open_email_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Send meeting notes")
        dlg.configure(bg=BG_CARD)
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)

        tk.Label(dlg, text="Send meeting notes",
                 fg=TEXT_PRI, bg=BG_CARD,
                 font=("SF Pro Display", 12, "bold"),
                 pady=12).pack()

        tk.Label(dlg, text="Recipients (comma-separated)",
                 fg=TEXT_SEC, bg=BG_CARD,
                 font=("SF Pro Display", 10)).pack(anchor="w", padx=16)

        entry = tk.Entry(dlg, bg=BG_PILL, fg=TEXT_PRI,
                         insertbackground=ACCENT,
                         relief="flat", font=("SF Pro Display", 10),
                         width=32)
        entry.pack(padx=16, pady=(4, 12), ipady=6)

        btn_row = tk.Frame(dlg, bg=BG_CARD)
        btn_row.pack(pady=(0, 14))

        def _do_send():
            recipients = [r.strip() for r in entry.get().split(",") if r.strip()]
            if not recipients:
                return
            dlg.destroy()
            threading.Thread(
                target=self._do_send_email,
                args=(recipients,), daemon=True).start()

        PillButton(btn_row, "Send", _do_send,
                   color=ACCENT, width=80).pack(side="left", padx=(16, 6))
        PillButton(btn_row, "Cancel", dlg.destroy,
                   color=BG_PILL, text_color=TEXT_SEC, width=80).pack(side="left")

    def _do_send_email(self, recipients):
        try:
            from delivery.email_sender import create_email_sender_from_config
            sender = create_email_sender_from_config()
            sender.send_followup_sync(self.intelligence, recipients)
            self.root.after(0, lambda: self._set_status("Email sent ✓", ACCENT))
        except Exception as ex:
            self.root.after(0, lambda: messagebox.showerror("Email failed", str(ex)))

    def _copy_notes(self):
        if not self.intelligence:
            messagebox.showwarning("No data", "Process a recording first.")
            return
        intel = self.intelligence
        lines = [f"# {intel.summary.title}", "",
                 intel.summary.summary, "",
                 "## Action items"]
        for item in intel.action_items:
            owner = f" ({item.owner})" if item.owner else ""
            lines.append(f"- [ ] {item.task}{owner}")
        lines += ["", "## Decisions"]
        for dec in intel.decisions:
            lines.append(f"- {dec.decision}")
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        self._set_status("Copied ✓", ACCENT)

    # ── progress animation ────────────────────────────────────────────────────

    def _show_progress(self):
        self.result_card.pack_forget()
        self.progress_card.pack(fill="x", pady=(0, 6))

    def _set_prog(self, msg):
        self.root.after(0, lambda: self._prog_lbl.config(text=msg))

    def _start_progress_anim(self):
        self._prog_w = 0
        self._prog_forward = True
        self._animate_prog()

    def _animate_prog(self):
        self._prog_bar.update_idletasks()
        total = self._prog_bar.winfo_width()
        if total < 2:
            self._prog_anim_id = self.root.after(50, self._animate_prog)
            return
        step = 3
        if self._prog_forward:
            self._prog_w = min(self._prog_w + step, total)
            if self._prog_w >= total:
                self._prog_forward = False
        else:
            self._prog_w = max(self._prog_w - step, 0)
            if self._prog_w <= 0:
                self._prog_forward = True
        self._prog_bar.coords(self._prog_fill, 0, 0, self._prog_w, 3)
        self._prog_anim_id = self.root.after(16, self._animate_prog)

    def _stop_progress_anim(self):
        if self._prog_anim_id:
            self.root.after_cancel(self._prog_anim_id)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, text, color=TEXT_SEC):
        self.root.after(0, lambda: self.status_lbl.config(
            text=text, fg=color))

    def _minimise(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(500, lambda: self.root.overrideredirect(True))

    def _on_close(self):
        if self.recording:
            if not messagebox.askyesno(
                    "Recording active", "Stop recording and exit?"):
                return
            self._stop_recording()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

def main():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.chdir(root)
    app = MeetingWidget()
    app.run()


if __name__ == "__main__":
    main()
