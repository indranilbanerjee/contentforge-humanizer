---
name: humanizer
description: "Edit your own draft so it reads naturally and specifically: ground vague claims in real specifics, delete filler and 'here's the thing' marker sentences, strip the tells of unedited AI drafting (43-pattern catalog), and keep the author's own sentences verbatim. Includes a stdlib-only scan (scripts/ai_tell_scan.py) that rates a draft LOW, MODERATE or HIGH and lists the sentences worth a second look. Use when asked to humanize a draft, make writing sound less robotic, generic or AI-ish, remove AI tells, cut padding from copy, or find what makes a draft read as machine-made. Triggers: humanize this, make this sound human, remove AI tells, this sounds like ChatGPT, de-AI my draft, edit my draft, ai tell scan. Not a detector for judging other people's writing."
license: MIT
compatibility: "Needs Python 3.9+ (standard library only) to run the scan; the editing method works without it."
metadata:
  author: Indranil Banerjee
  version: "1.0.0"
---

# Humanizer

This skill helps a writer edit their own draft so it reads naturally and specifically; it is not an AI detector for judging anyone else's writing, it makes no claim to beat or bypass any detector, and it neither detects nor removes watermarks.

## The goal

**Human-expert grounding: specificity, inline sourcing, technical-broad balance, and irregularity that comes from the content.** Generic prose is what an unedited model writes by default, and readers feel it before they can name it. The fix is better writing: name the thing, the date, the source, the number, and say what you actually think. A lower scan rating is a side effect of that, never the target.

## What you need

- **The draft** (a file path, or pasted text; save pasted text to a file or pipe it to the scan on stdin).
- **Optional, ask for them if they would change the edit:**
  - which sentences are the writer's own words (an original version to protect);
  - a writing sample of the voice to match;
  - the notes, sources and facts the writer can supply. These are the only permitted source of added specifics;
  - keywords, headings, tables, numbered steps or FAQ blocks that must survive;
  - the voice: authoritative, conversational, technical, or witty.

## Ground rules

1. **Do not change facts, numbers, quotes or citations.** This is a style pass.
2. **Never invent a specific.** Every number, date, source, quote, name or example you add must come from the draft itself or from material the writer gave you. If grounding is missing, add one calibrated caveat, leave the sentence, or ask the writer. A fabricated detail is worse than a generic sentence.
3. **Delete, do not reword, filler.** A sentence that carries no information is cut, not rephrased into different filler of the same length. Rephrased filler is still filler.
4. **Protected text stays word for word.** Sentences the writer says are theirs, and any wording a fact-checker or editor has already corrected, are never paraphrased, condensed, merged or grammar-fixed. See Step 0.
5. **Surgical edits.** One targeted change per problem. Do not rewrite a draft that mostly works.

## Method

### Step 0. Protect what is not yours to change

**The writer's own sentences.** If the writer supplied an original version or marked sentences as theirs:

- Never paraphrase, condense, merge or grammar-fix them, even when they are clumsy. Typos, run-ons, lowercase and odd word choices are the voice; "improving" them deletes the authorship.
- The 43-pattern catalog does not apply to them. If the writer wrote "here's the thing", it stays. The patterns describe what a model writes unprompted, not what a person chose to say.
- Add your material between their sentences: grounding, sourced specifics, transitions, sections they only gestured at.
- If a protected sentence looks factually wrong, do not rewrite it. Flag it in the report for the writer and leave it alone.
- After the pass, check the promise: every protected sentence must still appear in the final draft verbatim (search for each one). Restore any that moved, then check again.

**Already-corrected wording.** If a fact-checker or the writer fixed a sentence, that exact wording survives your pass. A style rewrite must not undo an accuracy correction. If it reads awkwardly, say so in the report and leave it.

**Protected structure and keywords.** Tables, numbered steps, Q&A and definition blocks, FAQ headers and required keyword placements stay in their form. Patterns 10, 16, 33, 34 and 39 and any list-to-prose rewrite do not apply inside them. Humanize the prose around them. Their wording may be tuned for voice; their form may not change.

### Step 1. Baseline scan

Run the scan (see "Running the scan") and keep the result. Note the rating, the flagged sentences and any `uniform_runs`. This is your map, not your checklist.

### Step 2. Voice calibration (only when a writing sample exists)

Study the sample before applying any voice. Note: sentence-length pattern (short and punchy, long and flowing, mixed); word level (casual "stuff, things" or academic "elements, components"); punctuation habits (dashes, parentheses, semicolons, fragments); how paragraphs open; two or three recurring phrases; how transitions are made (explicit "However," or just starting the next point).

Then **match them, do not merely remove tells.** Replace a removed pattern with a pattern from the sample. If the writer says "stuff", do not upgrade it to "elements".

### Step 3. Pattern sweep (the 43-pattern catalog)

The full catalog, with phrases to watch and before/after examples, is in `patterns.json` under `signs_of_ai_writing_catalog`. Walk every group; for each pattern scan the draft, flag matches, and apply the fix. Patterns 30 to 43 live in the draft's shape and rhetoric rather than its word choice, so check them against the finished piece, not sentence by sentence.

**Content**
- **01 Significance inflation**: "stands as", "testament to", "pivotal moment", "evolving landscape". Strip the puffery; say what the thing is and does.
- **02 Notability puffery**: bare lists of outlets or credentials. Give one specific, citable claim.
- **03 Superficial -ing analysis**: trailing "highlighting…", "ensuring…", "reflecting…". Delete the clause.
- **04 Promotional language**: "nestled", "vibrant", "boasts", "rich heritage". Use concrete facts.
- **05 Vague attribution**: "experts argue", "industry reports". Name the source or cut it.
- **06 Challenges-and-outlook formula**: "Despite challenges, X thrives". Give sourced specifics or cut it.

**Language and grammar**
- **07 AI vocabulary**: delve, intricate, tapestry, testament, seamless, leverage, and the rest of the list in `patterns.json` under `detector_lexicon`. Use the plain word.
- **08 Copula avoidance**: "serves as", "stands as", "boasts". Write "is" or "has".
- **09 Negative parallelism**: "Not just X, it's Y". State Y.
- **10 Rule-of-three overuse**: forced triplets. Use as many items as there really are.
- **11 Elegant variation**: one noun cycled through four synonyms. Repeat the noun, or use a pronoun.
- **12 False ranges**: "from X to Y" with no real scale. Write a plain list.
- **13 Passive or subjectless**: "No configuration needed". Name the actor.

**Style**
- **14 Em dash overuse**: more than 3 per 500 words. Swap most for commas, periods or parentheses; keep one or two.
- **15 Boldface overuse**: bold only where emphasis is earned.
- **16 Inline-header bullet lists**: "**Header:** text" lists. Use prose or real headings.
- **17 Title Case headings**: use sentence case unless house style says otherwise.
- **18 Emoji decoration**: remove from professional body copy.
- **19 Curly quotes**: straighten them, if house style uses straight quotes.

**Communication**
- **20 Chatbot artifacts**: "I hope this helps", "Let me know if". Delete.
- **21 Knowledge-cutoff disclaimers**: "as of my last update". Find the fact or remove the line.
- **22 Sycophantic tone**: "Great question!". Delete.

**Filler and hedging**
- **23 Filler phrases**: "in order to", "due to the fact that". Write "to", "because".
- **24 Excessive hedging**: "could potentially possibly". One qualifier at most.
- **25 Generic positive conclusions**: "the future looks bright". Give a specific fact or an open question.
- **26 Hyphenated word-pair overuse**: stacked modifiers like "data-driven cross-functional client-facing". Fewer, plainer words.
- **27 Persuasive authority tropes**: "at its core", "what really matters". State the point.
- **28 Signposting**: "Let's dive in", "Here's what you need to know". Start with the content.
- **29 Fragmented headers**: a heading plus a one-line restatement. Delete the restatement.

**Structure and framing**
- **30 Colon-subtitle headlines** (high signal): "X: Why Y Matters". Rewrite as one direct claim or question; keep a colon only when the subtitle adds information.
- **31 False-dichotomy openers**: "Whether you're a X or a seasoned Y". Delete the invented audience and open with substance.
- **32 Scene-setting openers**: "Picture this:". Tell a real, attributable story, or lead with the strongest fact.
- **33 Parallel H2 grammar**: every heading in one grammatical form. Vary the forms where the content allows; keep parallelism for genuinely coordinate sections such as numbered steps.
- **34 FAQ-shaped conclusions**: a bolted-on FAQ that restates the body. Delete it, unless it answers new questions or the piece is an FAQ.
- **35 Bottom-line headers**: "The Bottom Line", "Key Takeaways", recap bullets. Close with something new (a next step, a dated prediction, a named trade-off); cut recap bullets below about 2,000 words.

**Detector-signal patterns (rhetoric and information density)**
- **36 Aphoristic maxims** (high signal): short, polished, content-free "insight" lines such as "Speed wins the shelf." Ground the line with a specific from the writer's material, or delete it. Never leave a maxim standing alone.
- **37 Impersonal assertion**: "is well documented", "has been shown". Say who documented it.
- **38 Epistemic flatness**: the same confidence on every claim. Add one specific, defensible caveat where an expert would. Vague hedging is pattern 24; do not swap one tell for the other.
- **39 Perfect parallelism**: list items of identical shape and length. Break the symmetry with uneven lengths or an embedded aside.
- **40 Participial openers**: "Building on this,", "Leveraging the platform,". Open with the subject and the specifics.
- **41 Connective-opener density**: many sentences starting "So", "Moreover", "Furthermore". Open with subjects, specifics or data; aim for under about 10% of sentences.
- **42 Significance markers** (high signal): a sentence whose only job is to tell the reader what its neighbour means: "here's the thing", "that's the part that got me", "which is exactly the problem", "let that sink in", "here's where it gets interesting". **Delete it; do not reword it.** The specific it points at already does the work, and a gentler marker is the same tell. If the moment truly matters, return to the specific a second time instead of announcing it.
- **43 Soft-adverb feeling tags**: "honestly", "genuinely", "truly", "literally", "actually", "basically", "quietly" used to attach feeling instead of meaning, especially sentence-final. Delete. At most one in the whole piece, only where it does literal work, never sentence-final, never two in one sentence. A sentence that needs force needs a specific, not an adverb.

**Regulated fields** (health, finance, legal, education): replace hype ("cutting-edge treatment", "unlock value", "revolutionary approach") with mechanism names, citations and the regulated wording the field requires. Never add efficacy claims or guaranteed-outcome language, and keep required disclaimers.

Keep a **deletion ledger** as you go: every phrase or sentence removed outright, quoted verbatim, with its pattern number and a few words on why. A rewrite can only be judged by re-reading the whole piece; a cut list can be audited in seconds, and it teaches the writer what to stop typing.

### Step 4. Grounding pass (the master lever)

Walk the draft paragraph by paragraph. Specificity is the single most effective humanizing move, because no model predicts those exact details, and it is also simply better writing.

1. **Aphorism repair (36).** Ground each content-free "insight" line with the specific that motivated it (a number, date, agency, named example) from the writer's material, or delete it.
2. **Impersonal assertions (37).** Name who documents the claim, from the sources the writer gave you.
3. **Epistemic texture (38).** Where an expert would qualify, add one specific caveat with a concrete scope: "Timelines vary with agency workload; the 2024 cohort averaged nine months." In regulated fields these caveats are also the compliant choice.
4. **Technical-broad balance.** Where a technical term stands alone, pair it with a plain-language explanation in the same sentence.
5. **Journalistic grounding.** Where a claim floats free, attach event + date + named source inline.

**Hard rule, repeated because it is the one that matters:** specifics come only from the draft or the writer's material. No grounding available means a calibrated caveat, an unchanged sentence, or a question to the writer. Never invent a number, date, source, quote or example for style.

### Step 5. Rhythm, from content

Sentence-length variety is **advisory**, not a target. Manufactured variety is itself a tell: a run of inserted short punchy lines reads as machine-made to readers and to classifiers alike.

- Look at `uniform_runs` from the scan: five or more consecutive sentences within three words of each other feel robotic.
- Fix a run **from content the piece already earns**: split a long sentence at a natural qualification and let the caveat stand alone; fold a source clause or dated example into a short sentence to extend it; embed a plain-language aside where it truly clarifies.
- **Prohibited:** inserting content-free short sentences, maxims or fragments to move a number. If the content gives you nothing, leave the rhythm alone. Uniform but grounded beats varied but hollow.

### Step 6. Voice and openings

**Voice.** Use the writer's stated voice, or infer it from the draft; do not switch mid-piece.

| Voice | Techniques |
|---|---|
| Authoritative | Remove hedging ("seems to", "might"); data-first sentences; definitive statements; decisive conclusions |
| Conversational | Direct address ("you"); questions as transitions; contractions; informal transitions; personal asides |
| Technical | Keep the jargon; precision over simplicity; process-oriented; exact numbers, versions and specs |
| Witty (only if the voice calls for it) | Subtle wordplay, unexpected comparisons, self-aware asides; every joke earns its place; none in sensitive or regulated passages |

Look for two or three places per section where the voice can show up, and check each against any brand or compliance limits the writer gave.

**Openings.** Find three or more consecutive sentences that start the same way (same noun, same subject, same transition word) and rotate: subject-verb, prepositional phrase, adverb, dependent clause, question, number or data. No single opening pattern should account for more than about 30% of sentences.

**Conversational touches, sparingly.** One or two rhetorical questions per 500 words. Direct address only if the voice is second person. One or two parenthetical asides in the piece. Sentence fragments only when the writer's own sample uses them; an invented fragment is pattern 36.

### Step 7. Preservation check

Before finishing, confirm: protected sentences are verbatim (Step 0); required keywords are still where the writer needs them (a variance of up to two occurrences on the primary keyword is fine; a lost placement is not); protected structures kept their form; and readability did not get worse (shorter sentences usually improve it).

### Step 8. Self-critique pass

Reread the edited draft as a skeptical editor and answer: **"What still makes this read as machine-made?"** List two to five tells. Common ones:

- rhythm too tidy: clean contrasts, evenly paced paragraphs, no mess;
- a closer that ends on a slogan instead of a point;
- voice too neutral: no opinion, no mixed feeling, no first person where one would be natural;
- specifics that read like plausible placeholders (check every one against Ground Rule 2);
- a catalog pattern slipping through, most often copula avoidance (08), em dashes (14) and trailing -ing clauses (03);
- any sentence a generic model could have written, with no information unique to this piece.

Make **one targeted edit per tell.** If "no voice" is the tell, add soul from what the writer actually thinks: an opinion about a fact, an acknowledgment of complexity, a first-person observation where it fits, a specific feeling instead of a generic one ("there's something unsettling about X" beats "X is concerning"). Cap this at two or three instances per 1,000 words; more reads as performative. If the draft is the writer's voice, ask rather than invent the opinion.

### Step 9. Re-scan and report

Run the scan again on the final draft. Deliver **two separate things, never merged**:

1. **The edited draft**, body only, nothing appended. (A report stapled to the draft ends up published or counted as the draft's own prose.)
2. **An edit report:**
   - scan before and after: rating, and the numbers that moved;
   - patterns fixed, with a count per pattern;
   - the **deletion ledger** (verbatim table: `#` | deleted text | pattern | why);
   - every grounded addition and which of the writer's materials it came from;
   - items for the writer: protected sentences that look factually doubtful, and places where a real specific is missing and only the writer can supply it;
   - remaining flags and why each stays. A HIGH rating after editing needs a one-line explanation.

Optionally, `patterns.json` also carries a weighted tally (`ai_signal_scoring`: 7 high-signal patterns count double). If you report a number from it, say it is your own judgement and not a measurement.

#### A short worked example

Writer's notes: *the migration took three weeks; 40 tables moved; the downtime window was never used.*

> **Before:** Here's the thing: our migration took three weeks. Honestly, that's a testament to the team's seamless collaboration, ensuring zero downtime.
>
> **After:** The migration took three weeks and moved 40 tables, and we never used the downtime window.

| # | Deleted text | Pattern | Why |
|---|---|---|---|
| 1 | "Here's the thing:" | 42 | Points at the next sentence, which already carries the point |
| 2 | "Honestly," | 43 | Feeling tag, no meaning |
| 3 | "that's a testament to the team's seamless collaboration" | 01, 07 | Puffery; replaced by what happened, from the notes |
| 4 | ", ensuring zero downtime" | 03 | Trailing -ing clause; the fact survives as "never used the downtime window" |

Every specific in the "after" line is in the writer's notes. Nothing was invented.

## Running the scan

`<skill-dir>` is the folder that contains this SKILL.md.

```bash
python <skill-dir>/scripts/ai_tell_scan.py draft.md
python <skill-dir>/scripts/ai_tell_scan.py --file draft.md
cat draft.md | python <skill-dir>/scripts/ai_tell_scan.py -
```

Use `python3` where `python` is not Python 3. The script is standard library only, runs offline, reads only the file you give it plus `patterns.json` next to this SKILL.md, and prints JSON. Exit code 0 on success; exit 1 with an `error` key if the file is missing or unreadable.

If Python is not available, do the pattern sweep by reading, skip the scan, and say so in the report. Do not make up a rating.

## Reading the rating

Output fields:

| Field | Meaning |
|---|---|
| `advisory_rating` | `LOW`, `MODERATE` or `HIGH` (rules below) |
| `words_analyzed` | Words scanned. Under about 150 words, treat everything as noisy |
| `per_1000_words` | `banned_lexemes`, `significance_markers`, `soft_adverb_tags`, `aphorism_candidates`, `em_dashes`, each per 1,000 words |
| `connective_openers_pct` | Share of sentences opening with a connective (pattern 41) |
| `participial_openers_pct` | Share of sentences whose first word ends in "-ing" (pattern 40) |
| `significance_marker_count`, `soft_adverb_cluster_sentences` | Raw counts for patterns 42 and 43 |
| `uniform_runs` | Runs of five or more consecutive sentences of near-equal length: `start_sentence`, `length`, `mean_words` |
| `flagged_sentences` | Up to 25 sentences worth a second look, each with `index`, `text` and `tell`: `significance_marker` (42, with the `phrase`), `aphorism_candidate` (36), `connective_opener` (41), `banned_lexeme_cluster` (07, two or more lexicon words in one sentence), `soft_adverb_cluster` (43) |

**How the rating is set.** `HIGH` when any of these is true: `banned_lexemes` above 4.0 per 1,000 words; `significance_markers` above 1.5 per 1,000 (and at least 2 such sentences); `soft_adverb_tags` above 4.0 per 1,000 (and at least 3 uses); `connective_openers_pct` above 15. `MODERATE` when any of them passes half of its limit. `LOW` otherwise. The minimum counts exist so that one earned "actually" in a short piece is not turned into a rating by arithmetic.

`aphorism_candidates`, `em_dashes`, `participial_openers_pct` and `uniform_runs` are reported but do **not** drive the rating. The aphorism check cannot tell a content-free maxim ("Speed wins the shelf.") from a short factual sentence ("The neighbouring region barely moved."), so it is a prompt for your judgement, never a score.

**How to use it.**

- `LOW` means no loud surface habits. It does not mean the draft is specific, good, or written by a person.
- `MODERATE` or `HIGH`: open `flagged_sentences` and read them. Each is a question for you as the editor, not a verdict. A flagged sentence that earns its place can stay.
- Sentences are split on terminal punctuation, so a heading with no full stop merges into the sentence after it. Opener checks match whole words, so "Sometimes" is not a connective and "During" or "Something" is not a participle. Read flagged sentences before you act.
- The word lists are English. The scan sees surface habits only; the substantive tells (generic claims, no stance, template structure) need your reading, which is what Steps 4 and 8 are for.
- Do not delete sentences to lower a number. A rating moves when the writing improves.

For background on what detectors measure and why grounding beats evasion, see `references/ai-detection-signals.md`. It is shared word for word with the larger pipeline it was written for, so its file names and step labels belong to that pipeline; here the scan is `scripts/ai_tell_scan.py` and the catalog is `patterns.json`.

## What this is not

- **Not an AI detector.** The scan does not know who or what wrote a text. It has false positives on human writing and false negatives on edited AI output. Never use it to judge, grade or accuse anyone about their writing.
- **Not a way to beat or bypass any detector.** Do not tune a draft to any detector's score, and do not loop drafts through detectors. A detector score is advisory at best and fallible; better writing is the only durable result.
- **No watermark handling.** It does not detect, strip or defeat any watermark, and it reads visible text only.
- **Not a fact-checker or a source of facts.** It never supplies, changes or "improves" facts, numbers, quotes or citations.
- **Not a ghostwriter.** It edits what is there and asks the writer for what is missing.
- **Not a substitute for disclosure.** If a draft was written with AI help, editing it does not change that. Follow the disclosure rules wherever you publish.
- **Not the whole content pipeline.** Research, fact-checking and .docx delivery live in the full ContentForge plugin: https://github.com/indranilbanerjee/contentforge

Credit: the pattern catalog is adapted from Wikipedia's "Signs of AI writing" (WikiProject AI Cleanup, CC BY-SA), with structure influenced by blader/humanizer (MIT). The method and the scan are extracted from ContentForge's humanizer.
