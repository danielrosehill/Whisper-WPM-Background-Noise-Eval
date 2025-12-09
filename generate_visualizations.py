#!/usr/bin/env python3
"""Generate visualizations for Whisper ASR evaluation results."""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Load evaluation data
with open("results/eval_20251209_201142.json") as f:
    data = json.load(f)

# Process data
records = []
for item in data:
    word_count = item["metrics"]["reference_words"]
    duration = item["duration_seconds"]
    wpm = (word_count / duration) * 60
    wer = item["metrics"]["wer"] * 100  # Convert to percentage

    annotations = item.get("annotations", {})
    pace = annotations.get("pace", "unknown")
    background = annotations.get("background_noise", "unknown")
    mic_distance = annotations.get("mic_distance", "unknown")

    records.append({
        "id": item["id"],
        "sample": item["sample"],
        "wpm": wpm,
        "wer": wer,
        "pace": pace,
        "background": background,
        "mic_distance": mic_distance,
        "duration": duration
    })

# Create output directory
output_dir = Path("visualizations")
output_dir.mkdir(exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11

# Color palettes
pace_colors = {
    'slow': '#2ecc71',
    'normal': '#3498db',
    'quick': '#f39c12',
    'fast': '#e74c3c',
    'whispered': '#9b59b6',
    'loud': '#e67e22',
    'weird_voices': '#1abc9c',
    'unknown': '#95a5a6'
}

background_colors = {
    'none': '#2ecc71',
    'cafe': '#f39c12',
    'music': '#9b59b6',
    'convo_other': '#3498db',
    'convo_same': '#e74c3c',
    'convo_mixed': '#e67e22',
    'dogs': '#8e44ad',
    'baby': '#f1c40f',
    'honking': '#34495e',
    'siren': '#c0392b',
    'transit': '#16a085',
    'unknown': '#95a5a6'
}

# =============================================================================
# Figure 1: WPM vs WER Scatter Plot (colored by pace)
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

for record in records:
    color = pace_colors.get(record['pace'], '#95a5a6')
    ax.scatter(record['wpm'], record['wer'], c=color, s=100, alpha=0.7, edgecolors='white', linewidth=1)

# Add trend line
wpms = [r['wpm'] for r in records]
wers = [r['wer'] for r in records]
z = np.polyfit(wpms, wers, 1)
p = np.poly1d(z)
x_line = np.linspace(min(wpms), max(wpms), 100)
ax.plot(x_line, p(x_line), '--', color='#2c3e50', alpha=0.5, label=f'Trend (slope: {z[0]:.4f})')

ax.set_xlabel('Words Per Minute (WPM)', fontsize=12)
ax.set_ylabel('Word Error Rate (%)', fontsize=12)
ax.set_title('WPM vs Word Error Rate\n(colored by speaking pace annotation)', fontsize=14, fontweight='bold')

# Legend
legend_patches = [mpatches.Patch(color=color, label=pace.replace('_', ' ').title())
                  for pace, color in pace_colors.items() if any(r['pace'] == pace for r in records)]
ax.legend(handles=legend_patches, loc='upper right', title='Speaking Pace')

plt.tight_layout()
plt.savefig(output_dir / '01_wpm_vs_wer_by_pace.png', dpi=150, bbox_inches='tight')
plt.close()

# =============================================================================
# Figure 2: WPM vs WER Scatter Plot (colored by background noise)
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

for record in records:
    color = background_colors.get(record['background'], '#95a5a6')
    ax.scatter(record['wpm'], record['wer'], c=color, s=100, alpha=0.7, edgecolors='white', linewidth=1)

ax.set_xlabel('Words Per Minute (WPM)', fontsize=12)
ax.set_ylabel('Word Error Rate (%)', fontsize=12)
ax.set_title('WPM vs Word Error Rate\n(colored by background noise type)', fontsize=14, fontweight='bold')

# Legend
legend_patches = [mpatches.Patch(color=color, label=bg.replace('_', ' ').title())
                  for bg, color in background_colors.items() if any(r['background'] == bg for r in records)]
ax.legend(handles=legend_patches, loc='upper right', title='Background Noise')

plt.tight_layout()
plt.savefig(output_dir / '02_wpm_vs_wer_by_background.png', dpi=150, bbox_inches='tight')
plt.close()

# =============================================================================
# Figure 3: Average WER by Background Noise Type (Bar Chart)
# =============================================================================
background_wer = {}
for r in records:
    bg = r['background']
    if bg not in background_wer:
        background_wer[bg] = []
    background_wer[bg].append(r['wer'])

bg_avg = {bg: np.mean(wers) for bg, wers in background_wer.items()}
bg_sorted = sorted(bg_avg.items(), key=lambda x: x[1])

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh([x[0].replace('_', ' ').title() for x in bg_sorted],
               [x[1] for x in bg_sorted],
               color=[background_colors.get(x[0], '#95a5a6') for x in bg_sorted],
               edgecolor='white', linewidth=1)

ax.set_xlabel('Average Word Error Rate (%)', fontsize=12)
ax.set_title('Average WER by Background Noise Type\n(sorted lowest to highest)', fontsize=14, fontweight='bold')

# Add value labels
for bar, (bg, val) in zip(bars, bg_sorted):
    count = len(background_wer[bg])
    ax.text(val + 0.05, bar.get_y() + bar.get_height()/2,
            f'{val:.2f}% (n={count})', va='center', fontsize=10)

ax.set_xlim(0, max([x[1] for x in bg_sorted]) * 1.3)
plt.tight_layout()
plt.savefig(output_dir / '03_wer_by_background_noise.png', dpi=150, bbox_inches='tight')
plt.close()

# =============================================================================
# Figure 4: Average WER by Speaking Pace (Bar Chart)
# =============================================================================
pace_wer = {}
pace_wpm = {}
for r in records:
    pace = r['pace']
    if pace not in pace_wer:
        pace_wer[pace] = []
        pace_wpm[pace] = []
    pace_wer[pace].append(r['wer'])
    pace_wpm[pace].append(r['wpm'])

pace_avg = {pace: (np.mean(wers), np.mean(pace_wpm[pace])) for pace, wers in pace_wer.items()}
pace_sorted = sorted(pace_avg.items(), key=lambda x: x[1][0])

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh([x[0].replace('_', ' ').title() for x in pace_sorted],
               [x[1][0] for x in pace_sorted],
               color=[pace_colors.get(x[0], '#95a5a6') for x in pace_sorted],
               edgecolor='white', linewidth=1)

ax.set_xlabel('Average Word Error Rate (%)', fontsize=12)
ax.set_title('Average WER by Speaking Pace Annotation\n(sorted lowest to highest)', fontsize=14, fontweight='bold')

# Add value labels with WPM
for bar, (pace, (wer_val, wpm_val)) in zip(bars, pace_sorted):
    count = len(pace_wer[pace])
    ax.text(wer_val + 0.03, bar.get_y() + bar.get_height()/2,
            f'{wer_val:.2f}% @ {wpm_val:.0f} WPM (n={count})', va='center', fontsize=10)

ax.set_xlim(0, max([x[1][0] for x in pace_sorted]) * 1.5)
plt.tight_layout()
plt.savefig(output_dir / '04_wer_by_pace.png', dpi=150, bbox_inches='tight')
plt.close()

# =============================================================================
# Figure 5: WPM Distribution by Pace Annotation (Box Plot)
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

pace_data = {}
for r in records:
    if r['pace'] not in pace_data:
        pace_data[r['pace']] = []
    pace_data[r['pace']].append(r['wpm'])

# Sort by median WPM
pace_order = sorted(pace_data.keys(), key=lambda x: np.median(pace_data[x]))

box_data = [pace_data[p] for p in pace_order]
bp = ax.boxplot(box_data, labels=[p.replace('_', ' ').title() for p in pace_order],
                patch_artist=True, vert=False)

for patch, pace in zip(bp['boxes'], pace_order):
    patch.set_facecolor(pace_colors.get(pace, '#95a5a6'))
    patch.set_alpha(0.7)

ax.set_xlabel('Words Per Minute (WPM)', fontsize=12)
ax.set_title('WPM Distribution by Speaking Pace Annotation\n(validates pace labels against actual measured WPM)', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '05_wpm_distribution_by_pace.png', dpi=150, bbox_inches='tight')
plt.close()

# =============================================================================
# Figure 6: Heatmap - Background vs Pace
# =============================================================================
from collections import defaultdict

# Create matrix of average WER for each combination
combo_wer = defaultdict(list)
all_backgrounds = sorted(set(r['background'] for r in records))
all_paces = sorted(set(r['pace'] for r in records))

for r in records:
    combo_wer[(r['background'], r['pace'])].append(r['wer'])

# Create heatmap data
heatmap_data = np.zeros((len(all_backgrounds), len(all_paces)))
heatmap_data[:] = np.nan

for i, bg in enumerate(all_backgrounds):
    for j, pace in enumerate(all_paces):
        if (bg, pace) in combo_wer:
            heatmap_data[i, j] = np.mean(combo_wer[(bg, pace)])

fig, ax = plt.subplots(figsize=(14, 8))
im = ax.imshow(heatmap_data, cmap='RdYlGn_r', aspect='auto')

ax.set_xticks(np.arange(len(all_paces)))
ax.set_yticks(np.arange(len(all_backgrounds)))
ax.set_xticklabels([p.replace('_', ' ').title() for p in all_paces], rotation=45, ha='right')
ax.set_yticklabels([b.replace('_', ' ').title() for b in all_backgrounds])

# Add text annotations
for i in range(len(all_backgrounds)):
    for j in range(len(all_paces)):
        if not np.isnan(heatmap_data[i, j]):
            text = ax.text(j, i, f'{heatmap_data[i, j]:.2f}%',
                          ha='center', va='center', color='black', fontsize=9)

ax.set_title('Average WER by Background Noise × Speaking Pace\n(green = lower WER, red = higher WER)',
             fontsize=14, fontweight='bold')
cbar = ax.figure.colorbar(im, ax=ax)
cbar.set_label('WER (%)', rotation=270, labelpad=15)

plt.tight_layout()
plt.savefig(output_dir / '06_heatmap_background_pace.png', dpi=150, bbox_inches='tight')
plt.close()

# =============================================================================
# Figure 7: WER Distribution Overview (Histogram)
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

wer_values = [r['wer'] for r in records]
ax.hist(wer_values, bins=15, color='#3498db', edgecolor='white', linewidth=1, alpha=0.8)
ax.axvline(np.mean(wer_values), color='#e74c3c', linestyle='--', linewidth=2, label=f'Mean: {np.mean(wer_values):.2f}%')
ax.axvline(np.median(wer_values), color='#2ecc71', linestyle='--', linewidth=2, label=f'Median: {np.median(wer_values):.2f}%')

ax.set_xlabel('Word Error Rate (%)', fontsize=12)
ax.set_ylabel('Number of Recordings', fontsize=12)
ax.set_title('Distribution of Word Error Rates Across All Recordings', fontsize=14, fontweight='bold')
ax.legend()

plt.tight_layout()
plt.savefig(output_dir / '07_wer_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

# =============================================================================
# Figure 8: Sample Text Comparison
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

sample_wer = {}
sample_wpm = {}
for r in records:
    sample = r['sample'].replace('sample_0', 'Sample ').replace('_', ' ').title()
    if sample not in sample_wer:
        sample_wer[sample] = []
        sample_wpm[sample] = []
    sample_wer[sample].append(r['wer'])
    sample_wpm[sample].append(r['wpm'])

samples = list(sample_wer.keys())
x = np.arange(len(samples))
width = 0.35

fig, ax1 = plt.subplots(figsize=(10, 6))

bars1 = ax1.bar(x - width/2, [np.mean(sample_wer[s]) for s in samples], width,
                label='Avg WER (%)', color='#e74c3c', alpha=0.8)
ax1.set_ylabel('Average WER (%)', color='#e74c3c', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#e74c3c')

ax2 = ax1.twinx()
bars2 = ax2.bar(x + width/2, [np.mean(sample_wpm[s]) for s in samples], width,
                label='Avg WPM', color='#3498db', alpha=0.8)
ax2.set_ylabel('Average WPM', color='#3498db', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#3498db')

ax1.set_xlabel('Sample Text', fontsize=12)
ax1.set_xticks(x)
ax1.set_xticklabels(samples)
ax1.set_title('Performance Comparison by Sample Text', fontsize=14, fontweight='bold')

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}%',
             ha='center', va='bottom', fontsize=10)
for bar in bars2:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height, f'{height:.0f}',
             ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig(output_dir / '08_sample_text_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print(f"Generated 8 visualizations in {output_dir}/")
print("Files created:")
for f in sorted(output_dir.glob("*.png")):
    print(f"  - {f.name}")
