#!/usr/bin/env python3
"""
Simple audio recorder GUI for Whisper WPM Evaluation.
Records audio mapped to sample text files for speech-to-text testing.
"""

import json
import sys
import uuid
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QTextEdit, QGroupBox, QMessageBox,
    QSplitter, QFrame, QRadioButton, QButtonGroup, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Preferred microphone (partial match)
PREFERRED_MIC = "Samson Q2U"


class AudioRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whisper WPM & Background Noise Eval - Recorder")
        self.setMinimumSize(1000, 600)

        # Recording state
        self.is_recording = False
        self.is_paused = False
        self.has_unsaved_recording = False
        self.audio_data = []
        self.sample_rate = 16000  # 16kHz for Whisper
        self.channels = 1
        self.stream = None
        self.recording_start_time = None
        self.pause_start_time = None
        self.total_paused_time = 0

        # Paths
        self.base_path = Path(__file__).parent
        self.samples_path = self.base_path / "samples"
        self.recordings_path = self.base_path / "dataset"

        self.setup_ui()
        self.load_samples()
        self.load_audio_devices()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(15)

        # === LEFT PANE: Text to read ===
        left_pane = QFrame()
        left_pane.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_pane)

        text_label = QLabel("Text to Read")
        text_label.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
        left_layout.addWidget(text_label)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Sans Serif", 14))
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #fffef0;
                border: 1px solid #ccc;
                padding: 10px;
                line-height: 1.6;
            }
        """)
        left_layout.addWidget(self.text_display, 1)

        self.word_count_label = QLabel("Word count: 0")
        self.word_count_label.setStyleSheet("color: #666;")
        left_layout.addWidget(self.word_count_label)

        # === RIGHT PANE: Controls (scrollable) ===
        right_pane = QFrame()
        right_pane_layout = QVBoxLayout(right_pane)
        right_pane_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        right_layout = QVBoxLayout(scroll_content)
        right_layout.setSpacing(10)

        # Sample selection
        sample_group = QGroupBox("Sample Selection")
        sample_layout = QVBoxLayout(sample_group)
        sample_layout.addWidget(QLabel("Choose text:"))
        self.sample_combo = QComboBox()
        self.sample_combo.currentIndexChanged.connect(self.on_sample_changed)
        sample_layout.addWidget(self.sample_combo)
        right_layout.addWidget(sample_group)

        # Microphone selection
        mic_group = QGroupBox("Microphone")
        mic_layout = QVBoxLayout(mic_group)
        self.mic_combo = QComboBox()
        mic_layout.addWidget(self.mic_combo)
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.load_audio_devices)
        mic_layout.addWidget(self.refresh_btn)
        right_layout.addWidget(mic_group)

        # === ANNOTATIONS ===
        # Speaking pace
        pace_group = QGroupBox("Speaking Pace")
        pace_layout = QVBoxLayout(pace_group)
        self.pace_group = QButtonGroup(self)

        self.pace_options = [
            ("fast", "As fast as possible"),
            ("quick", "Quicker than normal"),
            ("normal", "Normal/conversational"),
            ("careful", "Careful enunciation"),
            ("slow", "Deliberately slow"),
            ("mumbled", "Mumbled/unclear"),
            ("whispered", "Whispered"),
            ("loud", "As loud as possible"),
            ("weird_voices", "Weird/altered voices"),
        ]

        for i, (value, label) in enumerate(self.pace_options):
            radio = QRadioButton(label)
            radio.setProperty("pace_value", value)
            self.pace_group.addButton(radio, i)
            pace_layout.addWidget(radio)
            if value == "normal":
                radio.setChecked(True)

        right_layout.addWidget(pace_group)

        # Mic distance
        distance_group = QGroupBox("Mic Distance")
        distance_layout = QVBoxLayout(distance_group)
        self.distance_group = QButtonGroup(self)

        self.distance_options = [
            ("close", "Close (< 6 inches)"),
            ("normal", "Normal (6-12 inches)"),
            ("far", "Far (> 12 inches)"),
        ]

        for i, (value, label) in enumerate(self.distance_options):
            radio = QRadioButton(label)
            radio.setProperty("distance_value", value)
            self.distance_group.addButton(radio, i)
            distance_layout.addWidget(radio)
            if value == "normal":
                radio.setChecked(True)

        right_layout.addWidget(distance_group)

        # Background noise (combo box for space efficiency)
        noise_group = QGroupBox("Background Noise")
        noise_layout = QVBoxLayout(noise_group)

        self.noise_options = [
            ("none", "None (quiet room)"),
            ("cafe", "Coffee shop/cafe"),
            ("office", "Busy office"),
            ("market", "Busy market"),
            ("music", "Background music"),
            ("music_vocals", "Music with vocals"),
            ("podcast_en", "Podcast (English)"),
            ("podcast_foreign", "Podcast (foreign language)"),
            ("convo_same", "Conversation (same language)"),
            ("convo_other", "Conversation (other language)"),
            ("convo_mixed", "Conversation (mixed languages)"),
            ("traffic", "Traffic (no honking)"),
            ("honking", "Traffic with honking"),
            ("siren", "Ambulance/emergency siren"),
            ("construction", "Construction noise"),
            ("dogs", "Dogs barking"),
            ("transit", "Public transit (bus/train)"),
            ("aircraft", "Aircraft/helicopter"),
            ("baby", "Baby crying/screaming"),
            ("wind", "Wind (outdoor)"),
            ("rain", "Rain/thunder"),
            ("other", "Other (see notes)"),
        ]

        self.noise_combo = QComboBox()
        for value, label in self.noise_options:
            self.noise_combo.addItem(label, value)
        noise_layout.addWidget(self.noise_combo)

        right_layout.addWidget(noise_group)

        # Notes field
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(
            "Optional notes: noise source, volume level, "
            "ambient conditions, etc."
        )
        self.notes_edit.setMaximumHeight(60)
        notes_layout.addWidget(self.notes_edit)
        right_layout.addWidget(notes_group)

        # Recording controls
        control_group = QGroupBox("Recording")
        control_layout = QVBoxLayout(control_group)

        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Monospace", 36, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(self.timer_label)

        # Start/Stop button
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.setMinimumHeight(50)
        self.record_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_btn)

        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setMinimumHeight(40)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setVisible(False)
        control_layout.addWidget(self.pause_btn)

        # Save/Discard buttons (shown after stopping)
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.save_recording)
        self.save_btn.setVisible(False)
        btn_row.addWidget(self.save_btn)

        self.discard_btn = QPushButton("Discard")
        self.discard_btn.setMinimumHeight(40)
        self.discard_btn.clicked.connect(self.discard_recording)
        self.discard_btn.setVisible(False)
        btn_row.addWidget(self.discard_btn)
        control_layout.addLayout(btn_row)

        self.update_button_styles()
        right_layout.addWidget(control_group)

        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(80)
        status_layout.addWidget(self.status_label)
        right_layout.addWidget(status_group)

        right_layout.addStretch()

        # Complete scroll area setup
        scroll_area.setWidget(scroll_content)
        right_pane_layout.addWidget(scroll_area)

        # Add panes to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_pane)
        splitter.addWidget(right_pane)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)

        # Timer for updating recording duration
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_timer_display)

    def load_audio_devices(self):
        """Load available input devices, preferring Samson Q2U."""
        self.mic_combo.clear()
        devices = sd.query_devices()
        default_input = sd.default.device[0]

        input_devices = []
        preferred_idx = None

        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                name = dev['name']
                input_devices.append((i, name))
                # Check for preferred mic
                if PREFERRED_MIC.lower() in name.lower() and "monitor" not in name.lower():
                    preferred_idx = len(input_devices) - 1

        for idx, name in input_devices:
            marker = ""
            if PREFERRED_MIC.lower() in name.lower() and "monitor" not in name.lower():
                marker = " [PREFERRED]"
            elif idx == default_input:
                marker = " [DEFAULT]"
            self.mic_combo.addItem(f"{name}{marker}", idx)

        # Select preferred mic, or fall back to default
        if preferred_idx is not None:
            self.mic_combo.setCurrentIndex(preferred_idx)
        else:
            for i in range(self.mic_combo.count()):
                if self.mic_combo.itemData(i) == default_input:
                    self.mic_combo.setCurrentIndex(i)
                    break

    def load_samples(self):
        """Load sample text files."""
        self.sample_combo.blockSignals(True)
        self.sample_combo.clear()
        self.samples = {}

        if self.samples_path.exists():
            for sample_file in sorted(self.samples_path.glob("*.txt")):
                name = sample_file.stem.replace("_", " ").title()
                with open(sample_file, 'r') as f:
                    self.samples[sample_file] = f.read()
                self.sample_combo.addItem(name, sample_file)

        self.sample_combo.blockSignals(False)

        if self.sample_combo.count() == 0:
            self.text_display.setText("No sample files found in samples/ directory.")
        else:
            self.on_sample_changed()

    def on_sample_changed(self):
        """Update text display when sample selection changes."""
        sample_path = self.sample_combo.currentData()
        if sample_path and sample_path in self.samples:
            text = self.samples[sample_path]
            self.text_display.setText(text)
            word_count = len(text.split())
            self.word_count_label.setText(f"Word count: {word_count} (~1 min at 150 WPM)")

    def update_button_styles(self):
        """Update button styles based on current state."""
        # Green start button
        green_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #45a049; }
        """
        # Red stop button
        red_style = """
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #da190b; }
        """
        # Orange pause button
        orange_style = """
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #f57c00; }
        """
        # Blue save button
        blue_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """
        # Gray discard button
        gray_style = """
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #616161; }
        """

        if self.is_recording:
            self.record_btn.setText("Stop")
            self.record_btn.setStyleSheet(red_style)
        else:
            self.record_btn.setText("Start Recording")
            self.record_btn.setStyleSheet(green_style)

        self.pause_btn.setStyleSheet(orange_style)
        self.save_btn.setStyleSheet(blue_style)
        self.discard_btn.setStyleSheet(gray_style)

    def toggle_recording(self):
        """Start or stop recording."""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def toggle_pause(self):
        """Pause or resume recording."""
        if self.is_paused:
            # Resume
            self.is_paused = False
            self.is_recording = True
            if self.pause_start_time:
                self.total_paused_time += (datetime.now() - self.pause_start_time).total_seconds()
            self.pause_btn.setText("Pause")
            self.status_label.setText("Recording... Read the text at a natural pace.")
        else:
            # Pause
            self.is_paused = True
            self.is_recording = False
            self.pause_start_time = datetime.now()
            self.pause_btn.setText("Resume")
            self.status_label.setText("Paused")

    def start_recording(self):
        """Start audio recording."""
        if self.sample_combo.currentData() is None:
            QMessageBox.warning(self, "No Sample", "Please select a sample text first.")
            return

        device_idx = self.mic_combo.currentData()
        if device_idx is None:
            QMessageBox.warning(self, "No Device", "Please select an input device.")
            return

        self.audio_data = []
        self.is_recording = True
        self.is_paused = False
        self.has_unsaved_recording = False
        self.total_paused_time = 0
        self.recording_start_time = datetime.now()

        # Update UI
        self.update_button_styles()
        self.pause_btn.setVisible(True)
        self.save_btn.setVisible(False)
        self.discard_btn.setVisible(False)
        self.status_label.setText("Recording... Read the text at a natural pace.")
        self.mic_combo.setEnabled(False)
        self.sample_combo.setEnabled(False)

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            if self.is_recording and not self.is_paused:
                self.audio_data.append(indata.copy())

        try:
            self.stream = sd.InputStream(
                device=device_idx,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=audio_callback,
                dtype=np.int16
            )
            self.stream.start()
            self.update_timer.start(100)
        except Exception as e:
            self.is_recording = False
            QMessageBox.critical(self, "Recording Error", f"Failed to start recording:\n{e}")
            self.reset_ui()

    def stop_recording(self):
        """Stop recording (does not save automatically)."""
        self.is_recording = False
        self.is_paused = False
        self.update_timer.stop()

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if self.audio_data:
            self.has_unsaved_recording = True
            duration = len(np.concatenate(self.audio_data)) / self.sample_rate
            self.status_label.setText(
                f"Recording stopped ({duration:.1f}s)\n"
                "Click Save to keep or Discard to retake."
            )
            # Show save/discard buttons
            self.pause_btn.setVisible(False)
            self.save_btn.setVisible(True)
            self.discard_btn.setVisible(True)
            self.update_button_styles()
            self.record_btn.setEnabled(False)
        else:
            self.status_label.setText("No audio data recorded.")
            self.reset_ui()

    def discard_recording(self):
        """Discard the current recording and reset."""
        self.audio_data = []
        self.has_unsaved_recording = False
        self.status_label.setText("Recording discarded. Ready for new recording.")
        self.reset_ui()

    def reset_ui(self):
        """Reset UI to initial state."""
        self.is_recording = False
        self.is_paused = False
        self.has_unsaved_recording = False
        self.update_button_styles()
        self.record_btn.setEnabled(True)
        self.pause_btn.setVisible(False)
        self.pause_btn.setText("Pause")
        self.save_btn.setVisible(False)
        self.discard_btn.setVisible(False)
        self.mic_combo.setEnabled(True)
        self.sample_combo.setEnabled(True)
        self.timer_label.setText("00:00")
        self.notes_edit.clear()

    def update_timer_display(self):
        """Update the recording timer display."""
        if self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def get_selected_pace(self):
        """Get the selected speaking pace value."""
        checked = self.pace_group.checkedButton()
        if checked:
            return checked.property("pace_value")
        return "normal"

    def get_selected_distance(self):
        """Get the selected mic distance value."""
        checked = self.distance_group.checkedButton()
        if checked:
            return checked.property("distance_value")
        return "normal"

    def get_selected_noise(self):
        """Get the selected background noise value."""
        return self.noise_combo.currentData() or "none"

    def get_selected_mic_name(self):
        """Get the name of the selected microphone."""
        return self.mic_combo.currentText().replace(" [PREFERRED]", "").replace(" [DEFAULT]", "")

    def save_recording(self):
        """Save recorded audio and metadata to file."""
        self.recordings_path.mkdir(exist_ok=True)
        audio_path = self.recordings_path / "audio"
        audio_path.mkdir(exist_ok=True)

        sample_path = self.sample_combo.currentData()
        sample_name = sample_path.stem if sample_path else "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_id = uuid.uuid4().hex[:4]

        # Get all annotations
        pace = self.get_selected_pace()
        distance = self.get_selected_distance()
        noise = self.get_selected_noise()
        mic_name = self.get_selected_mic_name()
        notes = self.notes_edit.toPlainText().strip()

        # Save audio to audio/ subfolder
        filename = f"{recording_id}.wav"
        filepath = audio_path / filename

        audio = np.concatenate(self.audio_data, axis=0)
        duration = len(audio) / self.sample_rate

        # Save audio
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())

        # Build metadata entry
        metadata = {
            "id": recording_id,
            "audio": f"audio/{filename}",
            "sample": sample_name,
            "sample_file": sample_path.name if sample_path else None,
            "word_count": len(self.samples.get(sample_path, "").split()) if sample_path else 0,
            "duration_seconds": round(duration, 2),
            "recorded_at": timestamp,
            "annotations": {
                "pace": pace,
                "mic_distance": distance,
                "background_noise": noise,
                "notes": notes if notes else None,
            },
            "equipment": {
                "microphone": mic_name,
                "sample_rate": self.sample_rate,
                "channels": self.channels,
            },
        }

        # Append to metadata.jsonl
        metadata_file = self.recordings_path / "metadata.jsonl"
        with open(metadata_file, 'a') as f:
            f.write(json.dumps(metadata) + "\n")

        # Clear recording data and reset UI
        self.audio_data = []
        self.has_unsaved_recording = False
        self.reset_ui()

        self.status_label.setText(
            f"Saved: {recording_id}\n"
            f"Pace: {pace} | Noise: {noise} | {duration:.1f}s"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AudioRecorder()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
