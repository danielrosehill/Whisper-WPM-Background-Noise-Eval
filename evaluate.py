#!/usr/bin/env python3
"""
Whisper ASR Evaluation Script

Transcribes audio files using Fireworks AI Whisper API and calculates WER
against ground truth using jiwer (standard ASR evaluation library).
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv
from jiwer import wer, cer

# Load .env file
load_dotenv()

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")
if not FIREWORKS_API_KEY:
    raise ValueError("FIREWORKS_API_KEY not found in environment")

# Paths
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
SAMPLES_DIR = BASE_DIR / "samples"
METADATA_FILE = DATASET_DIR / "metadata.jsonl"
RESULTS_DIR = BASE_DIR / "results"


def load_ground_truth(sample_file: str) -> str:
    """Load the ground truth text for a sample."""
    sample_path = SAMPLES_DIR / sample_file
    with open(sample_path) as f:
        return f.read().strip()


def load_metadata() -> list[dict]:
    """Load all recording metadata."""
    records = []
    with open(METADATA_FILE) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def normalize_text(text: str) -> str:
    """Normalize text for WER comparison."""
    # Lowercase
    text = text.lower()
    # Remove punctuation except apostrophes in contractions
    text = re.sub(r"[^\w\s']", "", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def transcribe_audio(audio_path: Path) -> str:
    """Transcribe audio using Fireworks AI Whisper API."""
    print(f"  Transcribing {audio_path.name}...", end=" ", flush=True)

    with open(audio_path, "rb") as f:
        response = requests.post(
            "https://audio-prod.api.fireworks.ai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {FIREWORKS_API_KEY}"},
            files={"file": f},
            data={
                "model": "whisper-v3",
                "temperature": "0",
                "vad_model": "silero"
            },
        )

    if response.status_code == 200:
        result = response.json()
        print("OK")
        return result.get("text", "")
    else:
        print(f"ERROR {response.status_code}")
        raise Exception(f"Transcription failed: {response.status_code} - {response.text}")


def calculate_metrics(reference: str, hypothesis: str) -> dict:
    """Calculate WER and CER metrics."""
    ref_norm = normalize_text(reference)
    hyp_norm = normalize_text(hypothesis)

    return {
        "wer": wer(ref_norm, hyp_norm),
        "cer": cer(ref_norm, hyp_norm),
        "reference_words": len(ref_norm.split()),
        "hypothesis_words": len(hyp_norm.split()),
    }


def run_evaluation():
    """Run full evaluation on all recordings."""
    print("Loading metadata...")
    records = load_metadata()
    print(f"Found {len(records)} recordings\n")

    # Cache ground truth texts
    ground_truths = {}

    results = []

    for i, record in enumerate(records, 1):
        record_id = record.get("id", "unknown")
        audio_rel_path = record.get("audio", f"audio/{record_id}.wav")
        audio_path = DATASET_DIR / audio_rel_path
        sample_file = record.get("sample_file", "")

        print(f"[{i}/{len(records)}] Processing {record_id}")

        if not audio_path.exists():
            print(f"  WARNING: Audio file not found: {audio_path}")
            continue

        # Get ground truth
        if sample_file not in ground_truths:
            ground_truths[sample_file] = load_ground_truth(sample_file)
        reference = ground_truths[sample_file]

        # Transcribe
        try:
            transcription = transcribe_audio(audio_path)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        # Calculate metrics
        metrics = calculate_metrics(reference, transcription)

        result = {
            "id": record_id,
            "sample": record.get("sample", ""),
            "sample_file": sample_file,
            "annotations": record.get("annotations", {}),
            "duration_seconds": record.get("duration_seconds", 0),
            "transcription": transcription,
            "reference": reference,
            "metrics": metrics,
        }
        results.append(result)

        print(f"  WER: {metrics['wer']:.2%} | CER: {metrics['cer']:.2%}")

    return results


def save_results(results: list[dict]):
    """Save evaluation results."""
    RESULTS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save detailed results as JSON
    results_file = RESULTS_DIR / f"eval_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")

    # Save transcripts separately
    transcripts_file = RESULTS_DIR / f"transcripts_{timestamp}.jsonl"
    with open(transcripts_file, "w") as f:
        for r in results:
            entry = {
                "id": r["id"],
                "transcription": r["transcription"],
                "wer": r["metrics"]["wer"],
            }
            f.write(json.dumps(entry) + "\n")
    print(f"Transcripts saved to: {transcripts_file}")

    # Generate summary
    if results:
        wers = [r["metrics"]["wer"] for r in results]
        cers = [r["metrics"]["cer"] for r in results]

        summary = {
            "timestamp": timestamp,
            "total_recordings": len(results),
            "avg_wer": sum(wers) / len(wers),
            "avg_cer": sum(cers) / len(cers),
            "min_wer": min(wers),
            "max_wer": max(wers),
            "by_pace": {},
            "by_background": {},
        }

        # Group by pace
        pace_groups = {}
        for r in results:
            pace = r["annotations"].get("pace", "unknown")
            if pace not in pace_groups:
                pace_groups[pace] = []
            pace_groups[pace].append(r["metrics"]["wer"])

        for pace, wers in pace_groups.items():
            summary["by_pace"][pace] = {
                "count": len(wers),
                "avg_wer": sum(wers) / len(wers),
            }

        # Group by background noise
        noise_groups = {}
        for r in results:
            noise = r["annotations"].get("background_noise", "unknown")
            if noise not in noise_groups:
                noise_groups[noise] = []
            noise_groups[noise].append(r["metrics"]["wer"])

        for noise, wers in noise_groups.items():
            summary["by_background"][noise] = {
                "count": len(wers),
                "avg_wer": sum(wers) / len(wers),
            }

        summary_file = RESULTS_DIR / f"summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved to: {summary_file}")

        # Print summary
        print("\n" + "=" * 50)
        print("EVALUATION SUMMARY")
        print("=" * 50)
        print(f"Total recordings: {summary['total_recordings']}")
        print(f"Average WER: {summary['avg_wer']:.2%}")
        print(f"Average CER: {summary['avg_cer']:.2%}")
        print(f"WER range: {summary['min_wer']:.2%} - {summary['max_wer']:.2%}")

        print("\nBy Speaking Pace:")
        for pace, stats in sorted(summary["by_pace"].items()):
            print(f"  {pace}: {stats['avg_wer']:.2%} (n={stats['count']})")

        print("\nBy Background Noise:")
        for noise, stats in sorted(summary["by_background"].items()):
            print(f"  {noise}: {stats['avg_wer']:.2%} (n={stats['count']})")


if __name__ == "__main__":
    results = run_evaluation()
    save_results(results)
