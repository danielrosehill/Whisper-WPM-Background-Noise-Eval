# Whisper WPM & Background Noise Evaluation

A "back of the envelope" evaluation intended to answer two questions I have about ASR/STT performance.

**Dataset**: [danielrosehill/ASR-WPM-And-Background-Noise-Eval](https://huggingface.co/datasets/danielrosehill/ASR-WPM-And-Background-Noise-Eval)



## Purpose

Create annotated audio recordings to evaluate how different factors affect Whisper transcription accuracy:
- Speaking pace (fast, normal, slow, mumbled, whispered)
- Background noise (cafe, office, market, conversations, traffic, wind)
- Microphone distance
- Different microphones

## Setup

```bash
# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Usage

```bash
./run.sh
# or
source .venv/bin/activate && python recorder.py
```

1. Select sample text and microphone
2. Choose annotations (pace, distance, background noise)
3. Add optional notes (noise source URL, volume level, etc.)
4. Record, review, then Save or Discard

## Annotations

**Speaking Pace:**
- As fast as possible
- Quicker than normal
- Normal/conversational
- Careful enunciation
- Deliberately slow
- Mumbled/unclear
- Whispered
- As loud as possible
- Weird/altered voices

**Mic Distance:**
- Close (< 6 inches)
- Normal (6-12 inches)
- Far (> 12 inches)

**Background Noise:**
- Silence
- Coffee shop/cafe
- Busy office
- Busy market
- Background music
- Conversation (same/other/mixed language)
- Traffic/street
- Wind (outdoor)
- Other (see notes)

## Output

Each recording saves:
- `{id}.wav` - 16kHz mono audio (4-char hex ID)
- `{id}.json` - metadata with all annotations

Example metadata:
```json
{
  "id": "a3f2",
  "sample": "sample_01_technology",
  "word_count": 138,
  "duration_seconds": 62.5,
  "annotations": {
    "pace": "normal",
    "mic_distance": "close",
    "background_noise": "cafe",
    "notes": "imissmycafe.com at 50% volume"
  },
  "equipment": {
    "microphone": "Samson Q2U Microphone",
    "sample_rate": 16000,
    "channels": 1
  }
}
```

## Directory Structure

```
.
├── recorder.py         # Recording GUI
├── run.sh              # Launcher script
├── requirements.txt    # Python dependencies
├── samples/            # Text samples to read
└── dataset/            # Saved audio + metadata
```
