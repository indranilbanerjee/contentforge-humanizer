# contentforge-humanizer

One skill: edit your own draft so it reads naturally and specifically, with a small offline scan that shows you which sentences still sound like an unedited AI draft.

This skill helps a writer edit their own draft so it reads naturally and specifically; it is not an AI detector for judging anyone else's writing, it makes no claim to beat or bypass any detector, and it neither detects nor removes watermarks.

It is the humanizer from [ContentForge](https://github.com/indranilbanerjee/contentforge), pulled out as a single Agent Skill that runs on any draft with no pipeline around it.

## What it does

- Walks a **43-pattern catalog** of the habits unedited AI drafting leaves behind: significance inflation, "not just X, it's Y", stacked em dashes, "here's the thing", maxims like "Speed wins the shelf.", and 38 more.
- Works **grounding first**: the fix for generic prose is a real specific from you (a number, a date, a source), never an invented one.
- **Deletes instead of rewording** filler and marker sentences, and keeps a **deletion ledger** so you can audit every cut in seconds.
- **Protects your own sentences.** Anything you wrote and marked as yours stays word for word, typos included.
- Ships `ai_tell_scan.py`, a **standard-library-only** scan that rates a draft `LOW`, `MODERATE` or `HIGH` and lists the sentences worth a second look. No network, no model calls, no dependencies.

## Install

With [skills.sh](https://skills.sh):

```bash
npx skills add indranilbanerjee/contentforge-humanizer
```

Or copy it by hand. The skill is the folder `skills/humanizer`; keep the folder name `humanizer`, because the Agent Skills standard requires it to match the skill's `name`.

```bash
git clone https://github.com/indranilbanerjee/contentforge-humanizer
# Claude Code, for all your projects:
cp -r contentforge-humanizer/skills/humanizer ~/.claude/skills/humanizer
# or for one project:
cp -r contentforge-humanizer/skills/humanizer .claude/skills/humanizer
```

Any other Agent Skills client: copy `skills/humanizer` into that client's skills directory. The scan needs Python 3.9 or newer; the editing method works without it.

## Use

Ask in plain language: "humanize this draft", "remove the AI tells from my post", "this sounds like ChatGPT, fix it", "run an ai tell scan on draft.md". Give it your notes and sources if you have them; they are the only material it is allowed to add specifics from. You get back the edited draft (body only) and a separate edit report with the before and after scan and the deletion ledger.

## The scan

```bash
python skills/humanizer/scripts/ai_tell_scan.py draft.md
```

Given this draft:

```text
Moreover, leveraging seamless workflows lets teams delve into the intricate tapestry of audience needs. Here's the thing: consistency matters. Speed wins the shelf. Honestly, it's a genuine testament to what is possible.
```

the scan prints (a real run, unedited):

```json
{
  "words_analyzed": 32,
  "per_1000_words": {
    "aphorism_candidates": 31.25,
    "banned_lexemes": 187.5,
    "em_dashes": 0.0,
    "significance_markers": 31.25,
    "soft_adverb_tags": 31.25
  },
  "connective_openers_pct": 25.0,
  "participial_openers_pct": 0.0,
  "significance_marker_count": 1,
  "soft_adverb_cluster_sentences": 0,
  "uniform_runs": [],
  "flagged_sentences": [
    {
      "index": 0,
      "text": "Moreover, leveraging seamless workflows lets teams delve into the intricate tapestry of audience needs.",
      "tell": "connective_opener"
    },
    {
      "index": 1,
      "text": "Here's the thing: consistency matters.",
      "tell": "significance_marker",
      "phrase": "here's the thing"
    },
    {
      "index": 2,
      "text": "Speed wins the shelf.",
      "tell": "aphorism_candidate"
    }
  ],
  "advisory_rating": "HIGH",
  "advisory_note": "Deterministic proxy scan — advisory only, never a publish gate. See references/ai-detection-signals.md."
}
```

Read it as an editor's map, not a verdict. Each flagged sentence is a question: does this one earn its place? `SKILL.md` explains every field and exactly how the rating is set. The scan also reads from stdin (`cat draft.md | python skills/humanizer/scripts/ai_tell_scan.py -`).

## What this is not

- **Not an AI detector.** It does not know who or what wrote a text, and it has false positives on human writing. Do not use it to judge or accuse anyone.
- **Not a way to beat or bypass any detector.** There is no detector integration and no rewrite loop against a score. A lower rating is a side effect of better writing.
- **No watermark handling.** It does not detect or remove watermarks; it reads visible text only.
- **Not a fact-checker.** It never invents or changes facts, numbers, quotes or citations. If a specific is missing it asks you for it.
- **Not the full pipeline.** For research, fact-checking and `.docx` delivery, use the whole thing: [ContentForge](https://github.com/indranilbanerjee/contentforge).

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests check the scan on three fixtures (an AI-sounding paragraph, a plain human paragraph, empty text), the 43-pattern catalog, the skill's frontmatter and links, and that the example above is a real run. When this repository sits next to a ContentForge checkout (`../../ContentForge`, or set `CONTENTFORGE_DIR`), they also prove **parity**: the scan output is identical to ContentForge's `text-metrics.py --ai-tell-scan` on the fixtures and on a corpus of real documents, the scan functions are the same code, and `patterns.json` is a verbatim copy. Without a ContentForge checkout those tests skip.

## Attribution and license

The pattern catalog (`skills/humanizer/patterns.json`) is adapted from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) by WikiProject AI Cleanup (CC BY-SA), with structure influenced by blader/humanizer (MIT). See the file's `_attribution` field.

MIT. See [LICENSE](LICENSE). Copyright (c) 2026 Indranil Banerjee.
