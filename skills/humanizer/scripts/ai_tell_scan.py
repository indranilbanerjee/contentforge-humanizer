#!/usr/bin/env python3
"""
ai_tell_scan.py
===============
A deterministic scan for the surface habits of unedited AI drafting, for a
writer editing THEIR OWN draft. Stdlib only. No network, no model calls.

This is the same scan ContentForge ships as `text-metrics.py --ai-tell-scan`,
extracted so this skill can run on its own. The scan logic is deliberately
identical (tests/test_scan.py proves it against ContentForge whenever the two
repositories sit side by side); only imports and file paths differ.

Usage:
    python ai_tell_scan.py draft.md
    python ai_tell_scan.py --file draft.md
    cat draft.md | python ai_tell_scan.py -

Output (JSON, printed to stdout; exit 0, or exit 1 with an "error" key):
    words_analyzed
    per_1000_words        {aphorism_candidates, banned_lexemes, em_dashes,
                           significance_markers, soft_adverb_tags}
    connective_openers_pct, participial_openers_pct
    significance_marker_count, soft_adverb_cluster_sentences
    uniform_runs          runs of 5+ consecutive sentences of near-equal length
    flagged_sentences     up to 25 sentences worth a second look, with the tell
    advisory_rating       LOW / MODERATE / HIGH
    advisory_note

Advisory only. It measures visible text habits; it is not an AI detector, it
cannot say who or what wrote a text, and it has no relationship to any
statistical watermark. Read skills/humanizer/references/ai-detection-signals.md.

The word lists live in ../patterns.json (`detector_lexicon`). The rating
thresholds are the six numbers in THRESHOLDS below.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The catalog ships one level up from scripts/, inside the skill folder.
PATTERNS_PATH = Path(__file__).resolve().parent.parent / "patterns.json"

# Rating thresholds. In ContentForge these live in config/scoring-thresholds.json
# (default.quality_gates.phase_6_5_humanizer.ai_tell_scan); a standalone skill has
# no such file, so the same six values are carried here. tests/test_scan.py
# compares them with ContentForge's copy whenever that repository is alongside.
THRESHOLDS = {
    "aphorism_per_1000_high": 3.0,
    "banned_lexemes_per_1000_high": 4.0,
    "connective_openers_pct_high": 15,
    "significance_markers_per_1000_high": 1.5,
    "soft_adverb_tags_per_1000_high": 4.0,
    "moderate_fraction": 0.5,
}


def _ensure_utf8_stdout() -> None:
    """Force UTF-8 (errors=replace) on stdout/stderr.

    Windows consoles default to cp1252; printing JSON containing em dashes or
    non-Latin text would otherwise raise UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _finish(result) -> None:
    """Print the result JSON and exit: 1 when the result carries an error,
    0 otherwise, so shell callers can trust $?."""
    _ensure_utf8_stdout()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    is_error = isinstance(result, dict) and "error" in result
    sys.exit(1 if is_error else 0)


def split_sentences(text: str) -> list[str]:
    """Split prose into sentences on terminal punctuation. The single
    sentence-splitting implementation for this scan."""
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s for s in (x.strip() for x in raw) if len(s.split()) >= 1]


def _load_detector_config():
    """Load the detector lexicon from patterns.json (next to SKILL.md) and the
    rating thresholds carried in THRESHOLDS."""
    with open(PATTERNS_PATH, encoding="utf-8") as f:
        lex = json.load(f)["detector_lexicon"]
    return lex, dict(THRESHOLDS)


# Personal and anaphoric pronouns. A sentence carrying one is context-dependent
# — it points at a speaker, a reader, or an earlier sentence — so it cannot be
# the self-contained general claim pattern 36 targets.
_PRONOUN_RE = re.compile(
    r"\b(?:i|me|my|mine|we|us|our|ours|you|your|yours|he|him|his|she|her|hers|"
    r"they|them|their|theirs|it|its|this|that|these|those)\b", re.I)


def is_aphorism_candidate(sentence: str) -> bool:
    """A short, self-contained, ungrounded general claim — "Speed wins the shelf."

    Pattern 36 targets broad over-neutral one-liners with no number, name, date
    or source. The <=9-word test alone is not enough: measured against published
    human essays it flagged ordinary short prose ("But pick something and get
    going.", "The next step is to notice them.") at ~13 per 1000 words. A maxim
    generalizes; a sentence that refers to you, me, or the sentence before it
    does not.
    """
    s = sentence.strip()
    words = s.split()
    if not s or len(words) > 9 or s.endswith("?"):
        return False
    if any(ch.isdigit() for ch in s):
        return False
    if re.search(r"\((?:[A-Z][\w.]*,?\s*\d{4}|\d+)\)|\[\d+\]", s):
        return False
    if any(w[:1].isupper() for w in words[1:]):
        return False
    if _PRONOUN_RE.search(s):
        return False
    # Opening with a coordinating conjunction continues the previous sentence,
    # which is the same context-dependence the pronoun test rules out.
    if words[0].lower().strip(",") in ("but", "and", "so", "or", "yet", "nor"):
        return False
    return s.endswith(".")


# Opening "-ing" words that are not participles. Without this, "During the
# night..." or "Something changed..." counted as participial openers.
_NON_PARTICIPLE_ING = frozenset({
    "during", "something", "nothing", "anything", "everything", "morning",
    "evening", "spring", "string", "thing", "things", "ceiling", "wedding",
    "sibling", "sterling", "offspring", "pudding", "darling", "notwithstanding",
})


def _connective_matcher(connectives):
    """Whole-word match at the start of a sentence. A bare prefix match let
    "so" fire on "Sometimes", "Soon", "Something" and "Software"."""
    alts = "|".join(r"\s+".join(re.escape(w) for w in c.split())
                    for c in sorted(connectives, key=len, reverse=True))
    return re.compile(rf"^(?:{alts})(?![\w'-])", re.I)


def _is_participial_opener(sentence: str) -> bool:
    words = sentence.strip().split()
    if not words:
        return False
    first = re.sub(r"[^a-z]", "", words[0].lower())
    return len(first) >= 5 and first.endswith("ing") and first not in _NON_PARTICIPLE_ING


def ai_tell_scan(text: str) -> dict:
    """Deterministic scan for the surface habits of unedited AI drafting.
    Advisory only — see references/ai-detection-signals.md."""
    lex, thr = _load_detector_config()
    sentences = split_sentences(text)
    words_total = max(1, len(re.findall(r"[\w'-]+", text)))
    per_k = 1000.0 / words_total

    lset = set(lex["llm_favored_words"])
    banned = sum(1 for w in re.findall(r"[A-Za-z'-]+", text) if w.lower() in lset)
    connective_re = _connective_matcher(lex["connective_openers"])
    conn = sum(1 for s in sentences if connective_re.match(s.strip()))
    part = sum(1 for s in sentences if _is_participial_opener(s))
    em_dashes = text.count("—") + text.count(" -- ")

    # Patterns 42/43. Markers are matched on a normalized sentence so that a
    # curly apostrophe ("here’s") counts the same as a straight one.
    markers = tuple(m.lower() for m in lex.get("significance_markers", ()))
    soft_set = set(w.lower() for w in lex.get("soft_adverb_tags", ()))

    flagged, aph, sig, soft_total, soft_cluster = [], 0, 0, 0, 0
    for i, s in enumerate(sentences):
        st = s.strip()
        norm = st.lower().replace("’", "'")
        hit_marker = next((m for m in markers if m in norm), None)
        soft_here = sum(1 for w in re.findall(r"[a-z']+", norm) if w in soft_set)
        soft_total += soft_here
        if soft_here >= 2:
            soft_cluster += 1
        if hit_marker:
            sig += 1
            flagged.append({"index": i, "text": st, "tell": "significance_marker",
                            "phrase": hit_marker})
        elif is_aphorism_candidate(s):
            aph += 1
            flagged.append({"index": i, "text": st, "tell": "aphorism_candidate"})
        elif connective_re.match(st):
            flagged.append({"index": i, "text": st, "tell": "connective_opener"})
        elif sum(1 for w in re.findall(r"[A-Za-z'-]+", st) if w.lower() in lset) >= 2:
            flagged.append({"index": i, "text": st, "tell": "banned_lexeme_cluster"})
        elif soft_here >= 2:
            flagged.append({"index": i, "text": st, "tell": "soft_adverb_cluster"})

    runs, i = [], 0
    lens = [len(s.split()) for s in sentences]
    while i < len(lens):
        j = i
        while j + 1 < len(lens) and abs(lens[j + 1] - lens[i]) <= 3:
            j += 1
        if j - i + 1 >= 5:
            runs.append({"start_sentence": i, "length": j - i + 1,
                         "mean_words": round(sum(lens[i:j + 1]) / (j - i + 1), 1)})
        i = j + 1

    n = max(1, len(sentences))
    metrics = {
        "aphorism_candidates": round(aph * per_k, 2),
        "banned_lexemes": round(banned * per_k, 2),
        "em_dashes": round(em_dashes * per_k, 2),
        "significance_markers": round(sig * per_k, 2),
        "soft_adverb_tags": round(soft_total * per_k, 2),
    }
    conn_pct = round(100.0 * conn / n, 1)
    # `aphorism_candidates` is deliberately NOT in this dict. The proxy cannot
    # separate a content-free maxim ("Speed wins the shelf.") from a short
    # factual sentence ("The neighbouring region barely moved."), and measured
    # against a published human essay and a real generated article it drove both
    # to HIGH. A signal too imprecise to gate on is too imprecise to drive a
    # rating. The count and the flagged sentences are still reported, and pattern
    # 36 is still enforced by the editor's own judgment, where a human-shaped
    # reading can tell the two apart.
    highs = {"banned_lexemes": thr["banned_lexemes_per_1000_high"],
             "significance_markers": thr["significance_markers_per_1000_high"],
             "soft_adverb_tags": thr["soft_adverb_tags_per_1000_high"]}
    # Absolute floors for patterns 42/43: in a short piece a single legitimate
    # "actually" normalizes to a large per-1000 figure. One earned use is not a
    # tell, and the scan must not manufacture one out of arithmetic.
    floors = {"significance_markers": 2, "soft_adverb_tags": 3}
    counts = {"significance_markers": sig, "soft_adverb_tags": soft_total}

    def _fires(key, threshold):
        if counts.get(key, floors.get(key, 0)) < floors.get(key, 0):
            return False
        return metrics[key] > threshold

    over_high = any(_fires(k, v) for k, v in highs.items()) or conn_pct > thr["connective_openers_pct_high"]
    over_mod = any(_fires(k, v * thr["moderate_fraction"]) for k, v in highs.items()) \
        or conn_pct > thr["connective_openers_pct_high"] * thr["moderate_fraction"]
    rating = "HIGH" if over_high else ("MODERATE" if over_mod else "LOW")

    return {"words_analyzed": words_total,
            "per_1000_words": metrics,
            "connective_openers_pct": conn_pct,
            "participial_openers_pct": round(100.0 * part / n, 1),
            "significance_marker_count": sig,
            "soft_adverb_cluster_sentences": soft_cluster,
            "uniform_runs": runs,
            "flagged_sentences": flagged[:25],
            "advisory_rating": rating,
            "advisory_note": "Deterministic proxy scan — advisory only, never a publish gate. See references/ai-detection-signals.md."}


def main():
    parser = argparse.ArgumentParser(
        description="Scan a draft you are editing for the surface habits of unedited AI "
                    "drafting (advisory; not an AI detector)")
    parser.add_argument("path", nargs="?", default=None,
                        help="Text or Markdown file to scan, or - to read stdin")
    parser.add_argument("--file", dest="file", default=None,
                        help="Same as the positional path")
    args = parser.parse_args()

    target = args.file if args.file is not None else args.path
    if target is None:
        parser.error("give a file to scan (a path, --file PATH, or - for stdin)")

    if target == "-":
        _ensure_utf8_stdout()
        try:
            raw = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
            # Same newline handling as reading a file in text mode.
            text = raw.replace("\r\n", "\n").replace("\r", "\n")
        except OSError as exc:
            _finish({"error": f"could not read stdin: {exc}"})
    else:
        path = Path(target).expanduser()
        if not path.is_file():
            _finish({"error": f"file not found: {path}",
                     "recovery": "Pass the path to the draft you are editing."})
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")   # a byte-order mark (PowerShell 5.1, Notepad) is not text
        except OSError as exc:
            _finish({"error": f"could not read {path}: {exc}"})

    _finish(ai_tell_scan(text))


if __name__ == "__main__":
    main()
