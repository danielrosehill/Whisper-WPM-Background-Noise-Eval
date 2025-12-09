# Whisper ASR Evaluation Results

Evaluation run: December 9, 2025

**Summary Statistics:**
- Total recordings: 40
- Average WER: 0.97%
- Average CER: 0.37%
- Best WER: 0.00%
- Worst WER: 2.90%
- WPM Range: 118 - 191 WPM

**Data Export:** [results.csv](results.csv)

---

## Results by Word Error Rate (Best to Worst)

| ID | Source | Pace | Mic Dist | Background | WPM | WER (%) |
|----|--------|------|----------|------------|-----|---------|
| 0587 | Technology | - | - | - | 138 | 0.00 |
| ce51 | Technology | Whispered | Far | None | 160 | 0.00 |
| 7acb | Nature | Whispered | Normal | None | 157 | 0.00 |
| 67bb | Nature | Normal | Normal | None | 156 | 0.00 |
| 8e25 | Nature | Slow | Normal | None | 118 | 0.00 |
| 6053 | Nature | Fast | Normal | Other lang | 153 | 0.00 |
| fad9 | Nature | Slow | Normal | None | 144 | 0.00 |
| 0502 | Nature | Loud | Normal | None | 172 | 0.00 |
| 3cdc | Technology | Weird voices | Normal | None | 140 | 0.72 |
| 6ba5 | Technology | Weird voices | Normal | None | 134 | 0.72 |
| c914 | Technology | Whispered | Normal | None | 154 | 0.72 |
| d124 | Technology | Normal | Normal | Cafe | 159 | 0.72 |
| e1c9 | Technology | Normal | Normal | Mixed conv | 159 | 0.72 |
| fc73 | Technology | Quick | Normal | None | 161 | 0.72 |
| 1dbd | Technology | Normal | Normal | Music | 152 | 0.72 |
| b25a | Technology | Normal | Normal | Music | 147 | 0.72 |
| 5220 | Technology | Normal | Normal | Honking | 154 | 0.72 |
| 1621 | Technology | Normal | Normal | Baby | 153 | 0.72 |
| 471e | Technology | Normal | Normal | Other lang | 148 | 0.72 |
| c919 | Technology | Normal | Normal | Other lang | 159 | 0.72 |
| 2207 | Technology | Normal | Normal | Other lang | 154 | 0.72 |
| 7a82 | Nature | Normal | Normal | Other lang | 161 | 0.71 |
| 0cc5 | Nature | Normal | Normal | Same lang | 153 | 0.71 |
| dd69 | Nature | Normal | Normal | None | 170 | 0.71 |
| d799 | Nature | Weird voices | Normal | None | 163 | 0.71 |
| 0d8d | Nature | Fast | Normal | None | 189 | 1.42 |
| dd63 | Nature | Quick | Normal | None | 196 | 1.42 |
| 4f14 | Nature | Quick | Normal | None | 174 | 1.42 |
| 8769 | Nature | Normal | Normal | None | 126 | 1.42 |
| 8aa1 | Nature | Normal | Normal | None | 129 | 1.42 |
| e8a7 | Nature | Normal | Normal | None | 167 | 1.42 |
| be48 | Technology | Fast | Normal | None | 188 | 1.45 |
| c2e8 | Technology | Normal | Normal | Dogs | 156 | 1.45 |
| 02b1 | Technology | Normal | Normal | Music | 146 | 1.45 |
| a15b | Technology | Normal | Normal | Other lang | 160 | 1.45 |
| 7951 | Technology | Slow | Normal | None | 121 | 2.17 |
| 265d | Technology | Normal | Normal | Other lang | 149 | 2.17 |
| 2ac3 | Technology | Normal | Normal | Transit | 157 | 2.17 |
| 6ae0 | Technology | Normal | Normal | Siren | 155 | 2.90 |
| d0d0 | Technology | Normal | Normal | Other lang | 153 | 2.90 |

---

## WPM vs WER Correlation Analysis

| WPM Range | Count | Avg WER (%) | Notes |
|-----------|-------|-------------|-------|
| < 130 | 4 | 0.90 | Slow speech |
| 130-150 | 9 | 0.89 | Moderate pace |
| 150-170 | 20 | 0.89 | Normal conversational |
| 170-190 | 5 | 0.85 | Quick speech |
| > 190 | 2 | 1.42 | Very fast speech |

**Observation:** There's a slight trend suggesting very fast speech (>190 WPM) may increase WER, but the sample size is small. Most recordings fall in the 150-170 WPM range with consistent performance.

---

## Key Findings by Speaking Pace (Subjective Annotation)

| Pace | Count | Avg WPM | Avg WER (%) |
|------|-------|---------|-------------|
| Loud | 1 | 172 | 0.00 |
| Whispered | 3 | 157 | 0.24 |
| Slow | 3 | 128 | 0.72 |
| Weird voices | 3 | 146 | 0.72 |
| Fast | 3 | 177 | 0.96 |
| Quick | 3 | 177 | 1.19 |
| Normal | 23 | 153 | 1.19 |

---

## Key Findings by Background Noise

| Background | Count | Avg WER (%) |
|------------|-------|-------------|
| None | 20 | 0.82 |
| Same language conversation | 1 | 0.71 |
| Cafe | 1 | 0.72 |
| Mixed conversation | 1 | 0.72 |
| Honking | 1 | 0.72 |
| Baby | 1 | 0.72 |
| Music | 3 | 0.97 |
| Other language conversation | 8 | 1.18 |
| Dogs barking | 1 | 1.45 |
| Transit | 1 | 2.17 |
| Siren | 1 | 2.90 |

---

## Sample Texts Used

**sample_01_technology (138 words):**
> The rapid advancement of artificial intelligence has transformed how we interact with technology in our daily lives...

**sample_02_nature (141 words):**
> The ancient forest stretched endlessly toward the horizon, its towering trees forming a cathedral of green...

---

## Methodology

- **ASR Engine**: Whisper (local deployment via Docker)
- **Audio Format**: 16kHz mono WAV
- **Evaluation Metric**: Word Error Rate (WER) using jiwer
- **WPM Calculation**: (word_count / duration_seconds) * 60
- **Speaker**: Single speaker (Daniel Rosehill)
- **Microphone**: Samson Q2U
