"""
Meeting Agent - Floating Widget
A always-on-top overlay for recording meetings and processing them locally.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import platform
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


# ── colour palette ────────────────────────────────────────────────────────────
BG          = "#1e1e2e"
BG_CARD     = "#2a2a3e"
ACCENT      = "#7c6af7"
ACCENT_DARK = "#5a4fd4"
RED         = "#f05050"
RED_DARK    = "#c03030"
GREEN       = "#50c878"
TEXT        = "#e0e0f0"
TEXT_DIM    = "#888aaa"
BORDER      = "#3a3a5a"


class RecordingTimer(threading.Thread):
    """Background thread that ticks the elapsed-time label."""

    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self.running = False
        self.start_time = None

    def run(self):
        self.running = True
        self.start_time = time.time()
        while self.running:
            elapsed = int(time.time() - self.start_time)
            m, s = divmod(elapsed, 60)
            self.callback(f"{m:02d}:{s:02d}")
            time.sleep(1)

    def stop(self):
        self.running = False


class MeetingWidget:
    """Floating always-on-top meeting recorder widget."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Meeting Agent")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Always on top
        self.root.attributes("-topmost", True)

        # Transparent background on supported platforms
        if platform.system() == "Windows":
            self.root.attributes("-alpha", 0.95)
        elif platform.system() == "Darwin":
            self.root.attributes("-alpha", 0.95)

        # Remove default title bar on all platforms for a cleaner look
        self.root.overrideredirect(True)

        # State
        self.recording = False
        self.mode = tk.StringVar(value="screen")   # screen | mic | system
        self.recorder = None
        self.timer_thread = None
        self.output_path = None
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self._position_top_right()
        self._bind_drag()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer frame with border
        outer = tk.Frame(self.root, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        main = tk.Frame(outer, bg=BG, padx=14, pady=10)
        main.pack(fill="both", expand=True)

        # ── title row ──
        title_row = tk.Frame(main, bg=BG)
        title_row.pack(fill="x", pady=(0, 8))

        tk.Label(title_row, text="⬤ ", fg=ACCENT, bg=BG,
                 font=("Helvetica", 10)).pack(side="left")
        tk.Label(title_row, text="Meeting Agent", fg=TEXT, bg=BG,
                 font=("Helvetica", 11, "bold")).pack(side="left")

        # close button
        close_btn = tk.Label(title_row, text="✕", fg=TEXT_DIM, bg=BG,
                             font=("Helvetica", 11), cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._on_close())

        # minimise button
        min_btn = tk.Label(title_row, text="─", fg=TEXT_DIM, bg=BG,
                           font=("Helvetica", 11), cursor="hand2")
        min_btn.pack(side="right", padx=(0, 6))
        min_btn.bind("<Button-1>", lambda e: self._minimise())

        # ── mode selector ──
        mode_row = tk.Frame(main, bg=BG)
        mode_row.pack(fill="x", pady=(0, 10))

        modes = [("🖥  Screen", "screen"), ("🎤  Mic", "mic"), ("🔊  System", "system")]
        for label, value in modes:
            rb = tk.Radiobutton(
                mode_row, text=label, variable=self.mode, value=value,
                bg=BG, fg=TEXT_DIM, selectcolor=BG,
                activebackground=BG, activeforeground=TEXT,
                font=("Helvetica", 9),
                indicatoron=False,
                relief="flat", bd=0,
                padx=8, pady=4,
                cursor="hand2",
                command=self._update_mode_buttons
            )
            rb.pack(side="left", padx=(0, 4))

        self._mode_buttons = mode_row.winfo_children()
        self._update_mode_buttons()

        # ── timer ──
        self.timer_label = tk.Label(main, text="00:00", fg=TEXT_DIM, bg=BG,
                                    font=("Courier", 22, "bold"))
        self.timer_label.pack(pady=(4, 8))

        # ── status ──
        self.status_label = tk.Label(main, text="Ready to record", fg=TEXT_DIM,
                                     bg=BG, font=("Helvetica", 9),
                                     wraplength=200, justify="center")
        self.status_label.pack(pady=(0, 10))

        # ── record / stop button ──
        self.rec_btn = tk.Button(
            main, text="⏺  Start Recording",
            bg=ACCENT, fg="white", activebackground=ACCENT_DARK,
            activeforeground="white", relief="flat", bd=0,
            font=("Helvetica", 10, "bold"),
            padx=16, pady=8, cursor="hand2",
            command=self._toggle_recording
        )
        self.rec_btn.pack(fill="x", pady=(0, 6))

        # ── process last recording ──
        self.process_btn = tk.Button(
            main, text="🧠  Process Last Recording",
            bg=BG_CARD, fg=TEXT_DIM, activebackground=BORDER,
            activeforeground=TEXT, relief="flat", bd=0,
            font=("Helvetica", 9),
            padx=12, pady=6, cursor="hand2",
            command=self._process_recording,
            state="disabled"
        )
        self.process_btn.pack(fill="x")

        # ── progress bar (hidden until processing) ──
        self.progress = ttk.Progressbar(main, mode="indeterminate", length=200)

        # ── result area (hidden until done) ──
        self.result_frame = tk.Frame(main, bg=BG_CARD, padx=10, pady=8)
        self.result_text = tk.Text(
            self.result_frame, bg=BG_CARD, fg=TEXT,
            font=("Helvetica", 8), relief="flat", bd=0,
            width=28, height=6, wrap="word",
            state="disabled"
        )
        self.result_text.pack(fill="both")

    def _update_mode_buttons(self):
        """Highlight the active mode radio button."""
        current = self.mode.get()
        for btn in self._mode_buttons:
            if isinstance(btn, tk.Radiobutton):
                val = btn.cget("value")
                if val == current:
                    btn.config(fg=TEXT, relief="solid", bd=1,
                               highlightbackground=ACCENT)
                else:
                    btn.config(fg=TEXT_DIM, relief="flat", bd=0)

    # ── window drag ───────────────────────────────────────────────────────────

    def _bind_drag(self):
        self.root.bind("<ButtonPress-1>", self._drag_start)
        self.root.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _position_top_right(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        w  = self.root.winfo_width()
        self.root.geometry(f"+{sw - w - 20}+40")

    # ── recording control ─────────────────────────────────────────────────────

    def _toggle_recording(self):
        if self.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        mode = self.mode.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            if mode == "screen":
                from capture.screen_recorder import ScreenRecorder
                self.recorder = ScreenRecorder()
                self.output_path = self.recorder.start(f"recording_screen_{timestamp}.mp4")

            elif mode == "mic":
                from capture.mic_recorder import MicRecorder
                self.recorder = MicRecorder()
                self.recorder.start()
                self.output_path = Path(f"recording_mic_{timestamp}.wav")

            elif mode == "system":
                from capture.system_audio import SystemAudioRecorder
                self.recorder = SystemAudioRecorder()
                self.recorder.start()
                self.output_path = Path(f"recording_system_{timestamp}.wav")

        except Exception as e:
            messagebox.showerror("Recording Error", str(e))
            return

        self.recording = True

        # Update UI
        self.rec_btn.config(text="⏹  Stop Recording", bg=RED,
                            activebackground=RED_DARK)
        self.timer_label.config(fg=RED)
        self.status_label.config(text=f"Recording ({mode})…", fg=RED)
        self.process_btn.config(state="disabled")

        # Start timer
        self.timer_thread = RecordingTimer(self._update_timer)
        self.timer_thread.start()

    def _stop_recording(self):
        self.recording = False

        # Stop timer
        if self.timer_thread:
            self.timer_thread.stop()

        # Stop recorder
        try:
            if self.mode.get() == "screen":
                self.output_path = self.recorder.stop()
            else:
                self.output_path = self.recorder.stop(str(self.output_path))
        except Exception as e:
            self._set_status(f"Stop error: {e}", TEXT_DIM)

        # Update UI
        self.rec_btn.config(text="⏺  Start Recording", bg=ACCENT,
                            activebackground=ACCENT_DARK)
        self.timer_label.config(fg=TEXT_DIM)
        self.process_btn.config(state="normal")
        self._set_status(f"Saved: {Path(self.output_path).name}", GREEN)

    def _update_timer(self, value: str):
        """Called from timer thread — schedule on main thread."""
        self.root.after(0, lambda: self.timer_label.config(text=value))

    # ── processing ────────────────────────────────────────────────────────────

    def _process_recording(self):
        if not self.output_path or not Path(self.output_path).exists():
            messagebox.showwarning("No Recording", "No recording file found.")
            return

        self.process_btn.config(state="disabled")
        self.progress.pack(fill="x", pady=(8, 0))
        self.progress.start(12)
        self._set_status("Processing… this may take a minute", TEXT_DIM)
        self.result_frame.pack_forget()

        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _run_pipeline(self):
        """Run the full pipeline in a background thread."""
        try:
            from capture.file_loader import FileLoader
            from processing.preprocessor import AudioPreprocessor
            from processing.transcriber import Transcriber
            from intelligence.pipeline import IntelligencePipeline
            from storage.database import Database

            path = FileLoader.load(str(self.output_path))

            self._set_status("Preprocessing audio…", TEXT_DIM)
            audio = AudioPreprocessor().process(path)

            self._set_status("Transcribing…", TEXT_DIM)
            transcript = Transcriber().transcribe(audio)

            self._set_status("Extracting intelligence…", TEXT_DIM)
            intelligence = IntelligencePipeline().process_sync(transcript['text'])

            db = Database()
            db.create_meeting({
                'title': intelligence.summary.title,
                'participants': intelligence.summary.participants,
                'duration_minutes': intelligence.summary.duration_minutes,
                'audio_file_path': str(self.output_path),
                'transcript': intelligence.transcript,
                'summary': intelligence.summary.summary,
                'key_points': intelligence.summary.key_points,
                'action_items': [i.dict() for i in intelligence.action_items],
                'decisions': [d.dict() for d in intelligence.decisions],
            })

            self.root.after(0, lambda: self._show_results(intelligence))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _show_results(self, intelligence):
        self.progress.stop()
        self.progress.pack_forget()

        title   = intelligence.summary.title
        items   = intelligence.action_items
        summary = intelligence.summary.summary

        lines = [f"📋 {title}\n"]
        lines.append(summary[:120] + ("…" if len(summary) > 120 else ""))
        if items:
            lines.append(f"\n✅ Action items ({len(items)}):")
            for item in items[:3]:
                lines.append(f"  • {item.task[:40]}")
            if len(items) > 3:
                lines.append(f"  … +{len(items)-3} more")

        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "\n".join(lines))
        self.result_text.config(state="disabled")
        self.result_frame.pack(fill="x", pady=(8, 0))

        self._set_status("Done — saved to database ✓", GREEN)
        self.process_btn.config(state="normal")

    def _show_error(self, msg: str):
        self.progress.stop()
        self.progress.pack_forget()
        self._set_status(f"Error: {msg[:60]}", RED)
        self.process_btn.config(state="normal")
        messagebox.showerror("Processing Error", msg)

    def _set_status(self, text: str, color: str = TEXT_DIM):
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

    # ── window controls ───────────────────────────────────────────────────────

    def _minimise(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(500, lambda: self.root.overrideredirect(True))

    def _on_close(self):
        if self.recording:
            if not messagebox.askyesno("Recording active",
                                       "Recording is in progress. Stop and exit?"):
                return
            self._stop_recording()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    # Make sure we can import project modules regardless of cwd
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Change to project root so config.yaml is found
    os.chdir(project_root)

    app = MeetingWidget()
    app.run()


if __name__ == "__main__":
    main()
