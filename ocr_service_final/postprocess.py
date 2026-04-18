"""
Post-processing for OCR output. Three layers:
  Layer 1 — char substitution rules (OCR confusion patterns)
  Layer 2 — fuzzy match against domain vocabulary from tesseract_metadata.csv
  Layer 3 — conservative spell correction (only high-confidence fixes)

Usage:
    from postprocess import clean, load_vocab
    vocab = load_vocab("./SimulatedNoisyOffice/tesseract_metadata.csv")
    result = clean(raw_text, vocab)

Standalone:
    python3 postprocess.py --text "The e eX St SeVeraI tnnethOdS" \
        --csv ./SimulatedNoisyOffice/tesseract_metadata.csv
"""

import re
import argparse
import csv
from pathlib import Path


# ── Layer 1: Char substitution rules ──────────────────────────────────────────

CHAR_RULES = [
    (r'(?<=[a-zA-Z])0(?=[a-zA-Z])', 'o'),   # 0 between letters → o
    (r'(?<=[a-zA-Z])1(?=[a-zA-Z])', 'l'),   # 1 between letters → l
    (r'(?<=[a-z])I(?=[a-z])',        'l'),   # I between lowercase → l
    (r'(?<=[a-z])S(?=[a-z])',        's'),   # S between lowercase → s
    (r'(?<=[a-z])O(?=[a-z])',        'o'),   # O between lowercase → o
    (r'(?<=[a-z])C(?=[a-z])',        'c'),   # C between lowercase → c
    (r'(?<=[a-z])U(?=[a-z])',        'u'),   # U between lowercase → u
    (r'(?<=[a-z])M(?=[a-z])',        'm'),   # M between lowercase → m
    (r'(?<=[a-z])N(?=[a-z])',        'n'),   # N between lowercase → n
    (r'(?<=[a-z])B(?=[a-z])',        'b'),   # B between lowercase → b
    (r'(?<=[a-z])D(?=[a-z])',        'd'),   # D between lowercase → d
    (r'(?<=[a-z])F(?=[a-z])',        'f'),   # F between lowercase → f
    (r'(?<=[a-z])G(?=[a-z])',        'g'),   # G between lowercase → g
    (r'(?<=[a-z])H(?=[a-z])',        'h'),   # H between lowercase → h
    (r'(?<=[a-z])R(?=[a-z])',        'r'),   # R between lowercase → r
    (r'(?<=[a-z])T(?=[a-z])',        't'),   # T between lowercase → t
    (r'(?<=[a-z])V(?=[a-z])',        'v'),   # V between lowercase → v
    (r'(?<=[a-z])W(?=[a-z])',        'w'),   # W between lowercase → w
    (r'(?<=[a-z])X(?=[a-z])',        'x'),   # X between lowercase → x
    (r'(?<=[a-z])Y(?=[a-z])',        'y'),   # Y between lowercase → y
    (r'rn',  'm'),
    (r'vv',  'w'),
    (r'VV',  'W'),
]


def apply_char_rules(text: str) -> str:
    for pattern, replacement in CHAR_RULES:
        text = re.sub(pattern, replacement, text)
    return text


# ── Layer 2: Domain vocabulary from CSV ───────────────────────────────────────

def load_vocab(csv_path: str) -> set[str]:
    """Extract all unique words from ground truth text in tesseract_metadata.csv."""
    vocab = set()
    path = Path(csv_path)
    if not path.exists():
        print(f"WARNING: vocab CSV not found at {csv_path}")
        return vocab

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get('text', '')
            words = re.findall(r"[a-zA-Z']+", text)
            for w in words:
                w_clean = w.strip("'").lower()
                if len(w_clean) >= 2:
                    vocab.add(w_clean)

    print(f"Domain vocab loaded: {len(vocab)} unique words")
    return vocab


def edit_distance(a: str, b: str) -> int:
    """Levenshtein distance between two strings."""
    if len(a) < len(b):
        return edit_distance(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j+1] + 1, curr[j] + 1,
                            prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def fuzzy_match(word: str, vocab: set[str], max_dist: int = 2) -> str | None:
    """
    Find closest vocab word within edit distance.
    Conservative — only returns match if unique and close enough.
    """
    word_lower = word.lower()

    # Exact match
    if word_lower in vocab:
        return None  # no correction needed

    # Only attempt correction for words >= 4 chars
    if len(word_lower) < 4:
        return None

    best_word = None
    best_dist = max_dist + 1

    for candidate in vocab:
        # Skip if length difference is too large
        if abs(len(candidate) - len(word_lower)) > max_dist:
            continue
        d = edit_distance(word_lower, candidate)
        if d < best_dist:
            best_dist = d
            best_word = candidate
        elif d == best_dist:
            best_word = None  # ambiguous — don't correct

    if best_word and best_dist <= max_dist:
        # Preserve original capitalisation
        if word[0].isupper():
            return best_word.capitalize()
        return best_word

    return None


def apply_domain_correction(text: str, vocab: set[str]) -> str:
    """Word-level fuzzy correction using domain vocabulary."""
    if not vocab:
        return text

    lines = text.split('\n')
    corrected = []

    for line in lines:
        tokens = line.split(' ')
        new_tokens = []
        for token in tokens:
            # Strip punctuation for matching but preserve it
            stripped = re.sub(r'[^a-zA-Z]', '', token)
            if len(stripped) >= 4:
                fix = fuzzy_match(stripped, vocab, max_dist=2)
                if fix:
                    token = token.replace(stripped, fix)
            new_tokens.append(token)
        corrected.append(' '.join(new_tokens))

    return '\n'.join(corrected)


# ── Layer 3: Conservative spell correction ────────────────────────────────────

def apply_spell_correction(text: str) -> str:
    """Only correct words with edit distance 1 and high confidence."""
    try:
        from spellchecker import SpellChecker
        spell = SpellChecker()
    except ImportError:
        return text

    lines = text.split('\n')
    corrected = []

    for line in lines:
        tokens = line.split(' ')
        new_tokens = []
        for token in tokens:
            stripped = re.sub(r'[^a-zA-Z]', '', token)
            # Very conservative — only fix words >= 5 chars, edit dist 1
            if len(stripped) >= 5 and stripped.lower() not in spell:
                candidates = spell.candidates(stripped.lower())
                if candidates:
                    best = min(candidates,
                               key=lambda c: edit_distance(c, stripped.lower()))
                    if edit_distance(best, stripped.lower()) == 1:
                        if token[0].isupper():
                            best = best.capitalize()
                        token = token.replace(stripped, best)
            new_tokens.append(token)
        corrected.append(' '.join(new_tokens))

    return '\n'.join(corrected)


# ── Public API ─────────────────────────────────────────────────────────────────

def clean(text: str, vocab: set = None, spell: bool = True) -> dict:
    """
    Returns dict with all three layers preserved:
      raw    — original OCR output
      layer1 — after char rules
      layer2 — after domain vocab fuzzy match
      layer3 — after conservative spell correction
    """
    layer1 = apply_char_rules(text)
    layer2 = apply_domain_correction(layer1, vocab or set())
    layer3 = apply_spell_correction(layer2) if spell else layer2

    return {
        "raw":    text,
        "layer1": layer1,
        "layer2": layer2,
        "layer3": layer3,
    }


# ── Standalone ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--csv",  default="./SimulatedNoisyOffice/tesseract_metadata.csv")
    parser.add_argument("--no-spell", action="store_true")
    args = parser.parse_args()

    vocab = load_vocab(args.csv)
    result = clean(args.text, vocab, spell=not args.no_spell)

    print(f"Raw:\n{result['raw']}\n")
    print(f"Layer 1 — char rules:\n{result['layer1']}\n")
    print(f"Layer 2 — domain vocab:\n{result['layer2']}\n")
    print(f"Layer 3 — spell correction:\n{result['layer3']}")
