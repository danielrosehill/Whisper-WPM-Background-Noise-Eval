---
license: mit
task_categories:
  - automatic-speech-recognition
language:
  - en
tags:
  - whisper
  - asr
  - speech-recognition
  - wer
  - evaluation
  - background-noise
  - speaking-pace
size_categories:
  - n<1K
---

# ASR WPM and Background Noise Evaluation Dataset

A dataset of annotated audio recordings designed to evaluate how different factors affect Whisper transcription accuracy.

## Dataset Description

This dataset contains 40 audio recordings with annotations for:

- **Speaking pace**: fast, normal, slow, whispered, weird voices, etc.
- **Background noise**: cafe, music, conversations (various languages), traffic, sirens, etc.
- **Microphone distance**: close, normal, far

Each recording is a reading of one of three sample texts (~140 words each) covering technology, nature, and history topics.

## Evaluation Results

Using Whisper v3 via Fireworks AI:

| Metric | Value |
|--------|-------|
| **Average WER** | 0.97% |
| **Average CER** | 0.37% |
| **WER Range** | 0.00% - 2.90% |

### By Speaking Pace

| Pace | WER | Count |
|------|-----|-------|
| Whispered | 0.24% | 3 |
| Slow | 0.72% | 3 |
| Weird voices | 0.72% | 3 |
| Fast | 0.96% | 3 |
| Normal | 1.19% | 23 |

### By Background Noise

| Noise Type | WER | Count |
|------------|-----|-------|
| None/silence | 0.82% | 20 |
| Cafe | 0.72% | 1 |
| Music | 0.97% | 3 |
| Conversation (other language) | 1.18% | 8 |
| Transit | 2.17% | 1 |
| Siren | 2.90% | 1 |

## Dataset Structure

```
dataset/
├── audio/           # WAV files (16kHz mono)
│   ├── {id}.wav
│   └── ...
└── metadata.jsonl   # Annotations for each recording
```

### Metadata Format

```json
{
  "id": "a3f2",
  "sample": "sample_01_technology",
  "sample_file": "sample_01_technology.txt",
  "word_count": 138,
  "duration_seconds": 52.5,
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
  },
  "audio": "audio/a3f2.wav"
}
```

## Key Findings

1. **Whisper v3 is remarkably robust** - average WER under 1% across all conditions
2. **Whispered speech performs surprisingly well** - lowest WER at 0.24%
3. **Background conversations in other languages** have minimal impact on accuracy
4. **Loud transient noises** (sirens, transit announcements) cause the most errors

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("danielrosehill/ASR-WPM-And-Background-Noise-Eval")
```

## Evaluation Code

The evaluation script and tools are available in the [GitHub repository](https://github.com/danielrosehill/Whisper-WPM-Background-Noise-Eval).

## License

MIT
