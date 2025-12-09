#!/usr/bin/env python3
"""Analyze transcripts for background language contamination."""

import json

# Load evaluation data
with open("results/eval_20251209_201142.json") as f:
    data = json.load(f)

# Focus on recordings with conversation backgrounds
conversation_backgrounds = ['convo_other', 'convo_same', 'convo_mixed']

print("=" * 80)
print("BACKGROUND LANGUAGE CONTAMINATION ANALYSIS")
print("=" * 80)

# Reference texts (cleaned)
ref_tech = set("""The rapid advancement of artificial intelligence has transformed how we interact
with technology in our daily lives From voice assistants that understand natural language to
recommendation systems that predict our preferences machine learning algorithms have become
invisible yet essential components of modern existence These systems analyze vast amounts of
data to identify patterns that would be impossible for humans to detect manually However this
technological progress also raises important questions about privacy bias and the future of
human employment As AI systems become more capable society must grapple with ethical
considerations about transparency and accountability The decisions these algorithms make can
affect everything from loan approvals to medical diagnoses making it crucial that we understand
their limitations and potential blind spots Balancing innovation with responsible development
remains one of the most significant challenges facing the technology industry today""".lower().split())

ref_nature = set("""The ancient forest stretched endlessly toward the horizon its towering trees
forming a cathedral of green that filtered the morning sunlight into soft golden beams Birds
called to one another across the canopy while small creatures rustled through the undergrowth
below This ecosystem had existed for thousands of years each species playing its vital role in
maintaining the delicate balance of life The forest floor was carpeted with fallen leaves that
decomposed slowly returning nutrients to the soil that fed the roots of giants above Streams
wound their way between moss covered rocks carrying fresh water to countless organisms that
depended on their flow Scientists have discovered that forests like this one communicate
through underground fungal networks sharing resources and warning signals between trees These
findings remind us that nature operates as an interconnected web rather than isolated
individuals competing for survival""".lower().split())

print("\n" + "=" * 80)
print("RECORDINGS WITH CONVERSATION BACKGROUNDS")
print("=" * 80)

for item in data:
    annotations = item.get("annotations", {})
    background = annotations.get("background_noise", "")
    notes = annotations.get("notes", "") or ""

    if background in conversation_backgrounds or "convo" in background:
        print(f"\n{'─' * 60}")
        print(f"ID: {item['id']}")
        print(f"Background: {background}")
        print(f"Notes: {notes}")
        print(f"WER: {item['metrics']['wer']*100:.2f}%")

        # Get reference and transcription
        ref = item['reference']
        trans = item['transcription']

        # Find differences
        ref_words = set(ref.lower().replace(',', '').replace('.', '').split())
        trans_words = set(trans.lower().replace(',', '').replace('.', '').split())

        # Words in transcription but not in reference
        extra_words = trans_words - ref_words
        # Words in reference but not in transcription
        missing_words = ref_words - trans_words

        if extra_words:
            print(f"\nWords ADDED (not in reference): {extra_words}")
        if missing_words:
            print(f"Words MISSING (in reference but not transcription): {missing_words}")

        # Check for specific language contamination patterns
        # Common words that might leak from background
        potential_contamination = []
        for word in extra_words:
            # Check if it's a real English word that doesn't belong
            if word not in ref_tech and word not in ref_nature:
                potential_contamination.append(word)

        if potential_contamination:
            print(f"\nPOTENTIAL CONTAMINATION: {potential_contamination}")

print("\n\n" + "=" * 80)
print("DETAILED COMPARISON: ENGLISH BACKGROUND CONVERSATIONS")
print("=" * 80)

# Find the English background one specifically
for item in data:
    annotations = item.get("annotations", {})
    notes = annotations.get("notes", "") or ""

    if "English" in notes or "American" in notes:
        print(f"\n{'─' * 60}")
        print(f"ID: {item['id']}")
        print(f"Notes: {notes}")
        print(f"WER: {item['metrics']['wer']*100:.2f}%")

        ref = item['reference']
        trans = item['transcription']

        # Word-by-word comparison
        ref_list = ref.split()
        trans_list = trans.split()

        print(f"\nRef word count: {len(ref_list)}")
        print(f"Trans word count: {len(trans_list)}")

        # Find the differences
        print("\nDifferences:")
        for i, (r, t) in enumerate(zip(ref_list, trans_list)):
            if r.lower().replace(',', '').replace('.', '') != t.lower().replace(',', '').replace('.', ''):
                print(f"  Position {i}: '{r}' -> '{t}'")

print("\n\n" + "=" * 80)
print("SIREN RECORDING ANALYSIS")
print("=" * 80)

for item in data:
    annotations = item.get("annotations", {})
    background = annotations.get("background_noise", "")

    if background == "siren":
        print(f"\nID: {item['id']}")
        print(f"WER: {item['metrics']['wer']*100:.2f}%")

        ref = item['reference']
        trans = item['transcription']

        print("\nDifferences found:")
        ref_list = ref.split()
        trans_list = trans.split()

        for i, (r, t) in enumerate(zip(ref_list, trans_list)):
            r_clean = r.lower().replace(',', '').replace('.', '')
            t_clean = t.lower().replace(',', '').replace('.', '')
            if r_clean != t_clean:
                # Get context (3 words before and after)
                start = max(0, i-3)
                end = min(len(ref_list), i+4)
                context_ref = ' '.join(ref_list[start:end])
                context_trans = ' '.join(trans_list[start:end])
                print(f"\n  Reference context: ...{context_ref}...")
                print(f"  Transcription:     ...{context_trans}...")
                print(f"  Change: '{r}' -> '{t}'")

print("\n\n" + "=" * 80)
print("SUMMARY: FOREIGN LANGUAGE BACKGROUNDS")
print("=" * 80)

foreign_lang_notes = []
for item in data:
    annotations = item.get("annotations", {})
    notes = annotations.get("notes", "") or ""
    background = annotations.get("background_noise", "")

    if background == "convo_other" and notes:
        foreign_lang_notes.append({
            'id': item['id'],
            'language': notes,
            'wer': item['metrics']['wer'] * 100,
            'ref': item['reference'],
            'trans': item['transcription']
        })

for entry in sorted(foreign_lang_notes, key=lambda x: x['wer']):
    print(f"\n{entry['language']}")
    print(f"  ID: {entry['id']}, WER: {entry['wer']:.2f}%")

    # Check for any contamination
    ref_words = set(entry['ref'].lower().replace(',', '').replace('.', '').split())
    trans_words = set(entry['trans'].lower().replace(',', '').replace('.', '').split())

    extra = trans_words - ref_words
    if extra:
        print(f"  Extra words in transcript: {extra}")
    else:
        print(f"  No foreign language contamination detected")
