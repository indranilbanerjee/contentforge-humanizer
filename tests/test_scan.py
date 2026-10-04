"""Tests for the standalone humanizer skill. Stdlib unittest only.

Run from the repository root:

    python -m unittest discover -s tests -v

Four layers:

  1. The scan runs on three fixtures (an AI-sounding paragraph, a plain human
     paragraph, empty text) and returns the documented keys and ratings.
  2. patterns.json loads and carries the 43-pattern catalog, counted the way
     ContentForge's own tests count it.
  3. The skill is self-contained and honest: frontmatter is valid, every
     file SKILL.md points at exists, nothing refers to pipeline files this
     repository does not have, the script imports only what it needs, the README
     example is a real run, and the framing sentence is present.
  4. PARITY with ContentForge. When ../../ContentForge (relative to the repo
     root; override with $CONTENTFORGE_DIR) is present, the scan output must be
     identical to ContentForge's `ai_tell_scan()` and `text-metrics.py
     --ai-tell-scan` on the fixtures, on a corpus of real ContentForge
     documents, and the scan functions must be the same code. Skipped
     otherwise, so a stand-alone clone still passes.

The parity tests only ever READ ContentForge; bytecode writing is disabled so
importing its modules cannot leave .pyc files behind there.
"""
import ast
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # parity imports ContentForge; never write into it

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "humanizer"
SCRIPT = SKILL / "scripts" / "ai_tell_scan.py"
PATTERNS = SKILL / "patterns.json"
REFERENCE = SKILL / "references" / "ai-detection-signals.md"
SKILL_MD = SKILL / "SKILL.md"
README = ROOT / "README.md"

CF_ROOT = Path(os.environ.get("CONTENTFORGE_DIR") or (ROOT / ".." / ".." / "ContentForge")).resolve()
CF_TEXT_METRICS = CF_ROOT / "scripts" / "text-metrics.py"
CF_PATTERNS = CF_ROOT / "config" / "humanization-patterns.json"
CF_THRESHOLDS = CF_ROOT / "config" / "scoring-thresholds.json"
CF_REFERENCE = CF_ROOT / "references" / "ai-detection-signals.md"
HAVE_CF = CF_TEXT_METRICS.is_file() and CF_PATTERNS.is_file() and CF_THRESHOLDS.is_file()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

AI_SOUNDING = (
    "In today's fast-paced digital landscape, content marketing has become a pivotal "
    "tool for brands. Moreover, leveraging seamless workflows allows teams to delve into "
    "the intricate tapestry of audience needs. Furthermore, harnessing data underscores "
    "the importance of a robust strategy. Here's the thing: consistency matters. Speed "
    "wins the shelf. Ultimately, success is a journey, not a destination. Additionally, "
    "brands that truly embrace change will genuinely thrive. Honestly, it's a testament "
    "to what is possible."
)

HUMAN_PLAIN = (
    "I started keeping the sourdough starter in the pantry in February, mostly because "
    "the fridge was full of my brother's beer. It was a mistake for about three weeks. "
    "The jar sat next to the radiator pipe, got too warm, and smelled like nail polish "
    "remover by the second Saturday. My neighbour Dolores, who has baked bread for forty "
    "years and does not own a scale, told me to pour off half and feed it flour and water "
    "twice a day until it calmed down. It did. The first loaf that came out of the oven "
    "was dense and lopsided but it tasted right, and I ate most of it standing at the "
    "counter."
)

EMPTY = ""

# Extra inputs for the parity corpus: they exercise branches the three main
# fixtures do not (curly apostrophes, em dashes, uniform runs, soft-adverb
# clusters, non-English text, whitespace-only input).
EXTRA_PARITY_TEXTS = {
    "whitespace_only": "  \n\n   \t ",
    "no_terminal_punctuation": "a heading with no full stop and no verb",
    "curly_markers": "Here’s the thing. Let that sink in. Honestly, it was truly remarkable — "
                     "and literally the best part? That’s the whole point.",
    "uniform_run": ("The team met on Monday to plan. The room was full of laptops. "
                    "Everyone brought a long list. The plan had seven main steps. "
                    "Each step had one clear owner. The owners agreed to the dates. "
                    "Nobody argued about the order."),
    "dashes_and_participles": ("Building on this -- and that — we shipped. Leveraging the platform, "
                               "teams moved faster — faster than before — and the numbers, "
                               "frankly, quietly improved. Using it daily, I noticed."),
    "non_english": "Das ist ein kurzer Satz. تجربة بسيطة. "
                   "これはテストです。 Moreover, c'est la vie.",
    "prefix_words": "Sometimes it rains. Soon it stops. Something changes. During the night we slept.",
}

DOCUMENTED_TOP_KEYS = {
    "words_analyzed", "per_1000_words", "connective_openers_pct",
    "participial_openers_pct", "significance_marker_count",
    "soft_adverb_cluster_sentences", "uniform_runs", "flagged_sentences",
    "advisory_rating", "advisory_note",
}
DOCUMENTED_METRIC_KEYS = {
    "aphorism_candidates", "banned_lexemes", "em_dashes",
    "significance_markers", "soft_adverb_tags",
}
TELL_NAMES = {
    "significance_marker", "aphorism_candidate", "connective_opener",
    "banned_lexeme_cluster", "soft_adverb_cluster",
}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read(path):
    return Path(path).read_text(encoding="utf-8")


def norm_eol(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


hero = load_module("hero_ai_tell_scan", SCRIPT)


def run_cli(args, stdin=None, cwd=None, script=SCRIPT):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, "-B", str(script), *args],
                          input=stdin, capture_output=True, cwd=cwd, env=env)
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


# ---------------------------------------------------------------------------
# 1. The scan on the three fixtures
# ---------------------------------------------------------------------------

class TestScanFixtures(unittest.TestCase):
    def assert_documented_shape(self, result):
        self.assertEqual(set(result), DOCUMENTED_TOP_KEYS)
        self.assertEqual(set(result["per_1000_words"]), DOCUMENTED_METRIC_KEYS)
        self.assertIn(result["advisory_rating"], {"LOW", "MODERATE", "HIGH"})
        self.assertIsInstance(result["words_analyzed"], int)
        self.assertIsInstance(result["uniform_runs"], list)
        self.assertIsInstance(result["flagged_sentences"], list)
        self.assertLessEqual(len(result["flagged_sentences"]), 25)
        for flag in result["flagged_sentences"]:
            self.assertIn(flag["tell"], TELL_NAMES)
            self.assertTrue({"index", "text", "tell"} <= set(flag))
        self.assertIn("advisory", result["advisory_note"].lower())
        json.dumps(result)  # serialisable

    def test_ai_sounding_paragraph(self):
        r = hero.ai_tell_scan(AI_SOUNDING)
        self.assert_documented_shape(r)
        self.assertEqual(r["advisory_rating"], "HIGH")
        self.assertGreater(r["per_1000_words"]["banned_lexemes"], 4.0)
        self.assertGreater(r["connective_openers_pct"], 15)
        self.assertEqual(r["significance_marker_count"], 1)
        tells = {f["tell"] for f in r["flagged_sentences"]}
        self.assertIn("significance_marker", tells)
        self.assertIn("aphorism_candidate", tells)
        self.assertIn("connective_opener", tells)

    def test_plain_human_paragraph(self):
        r = hero.ai_tell_scan(HUMAN_PLAIN)
        self.assert_documented_shape(r)
        self.assertEqual(r["advisory_rating"], "LOW")
        self.assertEqual(r["flagged_sentences"], [])
        self.assertEqual(r["uniform_runs"], [])
        self.assertEqual(r["per_1000_words"]["banned_lexemes"], 0.0)
        self.assertEqual(r["significance_marker_count"], 0)

    def test_empty_text(self):
        r = hero.ai_tell_scan(EMPTY)
        self.assert_documented_shape(r)
        self.assertEqual(r["advisory_rating"], "LOW")
        self.assertEqual(r["flagged_sentences"], [])
        self.assertEqual(r["uniform_runs"], [])
        self.assertEqual(r["connective_openers_pct"], 0.0)
        self.assertEqual(r["words_analyzed"], 1)  # floor of 1 avoids dividing by zero

    def test_ai_scores_worse_than_human_on_every_reported_signal(self):
        ai, human = hero.ai_tell_scan(AI_SOUNDING), hero.ai_tell_scan(HUMAN_PLAIN)
        for key in ("banned_lexemes", "aphorism_candidates", "significance_markers",
                    "soft_adverb_tags"):
            self.assertGreater(ai["per_1000_words"][key], human["per_1000_words"][key], key)
        self.assertGreater(ai["connective_openers_pct"], human["connective_openers_pct"])

    def test_single_earned_marker_in_a_short_piece_is_not_a_tell(self):
        # One "actually" normalises to a huge per-1000 figure in a short text;
        # the floors keep one earned use from becoming a rating.
        r = hero.ai_tell_scan("I actually liked the old layout better. The new one hides the search box.")
        self.assertEqual(r["advisory_rating"], "LOW")

    def test_uniform_run_detected(self):
        r = hero.ai_tell_scan(EXTRA_PARITY_TEXTS["uniform_run"])
        self.assertEqual(len(r["uniform_runs"]), 1)
        self.assertGreaterEqual(r["uniform_runs"][0]["length"], 5)

    def test_aphorism_heuristic(self):
        self.assertTrue(hero.is_aphorism_candidate("Speed wins the shelf."))
        self.assertFalse(hero.is_aphorism_candidate("Revenue rose 14% in Q2 2026."))
        self.assertFalse(hero.is_aphorism_candidate("What does the guidance require?"))
        self.assertFalse(hero.is_aphorism_candidate("But pick something and get going."))


# ---------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------

class TestCommandLine(unittest.TestCase):
    def test_cli_output_equals_in_process_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in (("ai", AI_SOUNDING), ("human", HUMAN_PLAIN), ("empty", EMPTY)):
                f = Path(tmp) / f"{name}.md"
                f.write_bytes(text.encode("utf-8"))
                for args in ([str(f)], ["--file", str(f)]):
                    with self.subTest(fixture=name, args=args[0]):
                        code, out, _ = run_cli(args, cwd=tmp)
                        self.assertEqual(code, 0)
                        self.assertEqual(json.loads(out), hero.ai_tell_scan(text))

    def test_stdin(self):
        code, out, _ = run_cli(["-"], stdin=AI_SOUNDING.encode("utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), hero.ai_tell_scan(AI_SOUNDING))

    def test_missing_file_is_an_error_not_a_traceback(self):
        code, out, err = run_cli([str(ROOT / "definitely-not-here.md")])
        self.assertEqual(code, 1)
        self.assertIn("error", json.loads(out))
        self.assertNotIn("Traceback", err)

    def test_skill_folder_is_relocatable(self):
        # patterns.json is found relative to the script, not the working directory,
        # so the skill works wherever an agent client copies it.
        with tempfile.TemporaryDirectory() as tmp:
            moved = Path(tmp) / "elsewhere" / "humanizer"
            shutil.copytree(SKILL, moved, ignore=shutil.ignore_patterns("__pycache__"))
            draft = Path(tmp) / "draft.md"
            draft.write_bytes(AI_SOUNDING.encode("utf-8"))
            code, out, _ = run_cli([str(draft)], cwd=tmp, script=moved / "scripts" / "ai_tell_scan.py")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out), hero.ai_tell_scan(AI_SOUNDING))


# ---------------------------------------------------------------------------
# 2. The catalog
# ---------------------------------------------------------------------------

class TestCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(read(PATTERNS))

    def test_catalog_has_43_patterns(self):
        # Counted exactly as ContentForge's tests do: numbered keys (NN_...) in
        # every dict bucket of signs_of_ai_writing_catalog that does not start "_".
        catalog = self.cfg["signs_of_ai_writing_catalog"]
        total = 0
        for bucket_name, bucket in catalog.items():
            if bucket_name.startswith("_") or not isinstance(bucket, dict):
                continue
            total += sum(1 for k in bucket if re.match(r"^\d{2}_", k))
        self.assertEqual(total, 43)

    def test_pattern_numbers_are_1_to_43_exactly_once(self):
        catalog = self.cfg["signs_of_ai_writing_catalog"]
        numbers = sorted(int(k[:2]) for b, v in catalog.items()
                         if not b.startswith("_") and isinstance(v, dict)
                         for k in v if re.match(r"^\d{2}_", k))
        self.assertEqual(numbers, list(range(1, 44)))

    def test_detector_signal_bucket_is_36_to_43(self):
        bucket = self.cfg["signs_of_ai_writing_catalog"]["detector_signal_patterns"]
        self.assertEqual({k[:3] for k in bucket if re.match(r"^\d{2}_", k)},
                         {f"{n}_" for n in range(36, 44)})

    def test_grounding_techniques_and_lexicon(self):
        techniques = {k for k in self.cfg["human_grounding_techniques"] if not k.startswith("_")}
        self.assertEqual(techniques, {"journalistic_grounding", "technical_broad_balance",
                                      "factual_clarity", "calibrated_expert_voice",
                                      "content_derived_variation"})
        lex = self.cfg["detector_lexicon"]
        for key in ("llm_favored_words", "connective_openers", "significance_markers",
                    "soft_adverb_tags"):
            self.assertTrue(lex[key], key)
        for word in ("delve", "tapestry"):
            self.assertIn(word, lex["llm_favored_words"])

    def test_script_reads_the_catalog_next_to_skill_md(self):
        self.assertEqual(hero.PATTERNS_PATH.resolve(), PATTERNS.resolve())


# ---------------------------------------------------------------------------
# 3. Self-containment, framing, and the README example
# ---------------------------------------------------------------------------

# Names of ContentForge pipeline files, phases and paths that do not exist here.
PIPELINE_ONLY = [
    r"phase[ -]?\d", r"text-metrics", r"humanization-patterns", r"authorship\.py",
    r"fix-ledger", r"build_review_sheet", r"scoring-thresholds", r"\.claude-marketing",
    r"CLAUDE_PLUGIN_ROOT", r"structure-manifest", r"source-draft", r"orchestrator",
    r"brand profile", r"Quality Gate", r"pipeline-tracker",
]

FRAMING = [
    (r"their own", "edits the writer's own draft"),
    (r"not an AI detector", "is not an AI detector"),
    (r"beat or bypass", "no claim to beat or bypass any detector"),
    (r"watermark", "no watermark detection or removal"),
]


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    assert m, "SKILL.md must open with a --- frontmatter block"
    fields = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if km:
            fields[km.group(1)] = km.group(2).strip()
    return fields, text[m.end():]


class TestSkillHygiene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = read(SKILL_MD)
        cls.fm, cls.body = frontmatter(cls.raw)

    def test_frontmatter(self):
        self.assertEqual(self.fm["name"], "humanizer")
        self.assertEqual(self.fm["name"], SKILL.name)  # must match the folder
        self.assertRegex(self.fm["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertEqual(self.fm["license"], "MIT")
        desc = self.fm["description"]
        self.assertTrue(desc.startswith('"') and desc.endswith('"'), "quote the description")
        desc = json.loads(desc)  # a double-quoted YAML scalar is valid JSON here
        self.assertTrue(0 < len(desc) <= 1024, len(desc))
        low = desc.lower()
        for needle in ("use when", "humaniz"):
            self.assertIn(needle, low)

    def test_description_does_not_claim_detection_or_bypass(self):
        low = json.loads(self.fm["description"]).lower()
        for banned in ("bypass", "undetect", "evade", "beat "):
            self.assertNotIn(banned, low)

    def test_every_file_skill_md_points_at_exists(self):
        refs = set(re.findall(r"(?<![\w/.-])((?:scripts|references)/[\w./-]+)", self.body))
        refs |= set(re.findall(r"(?<![\w/.-])(patterns\.json)", self.body))
        self.assertTrue(refs)
        for ref in sorted(refs):
            with self.subTest(ref=ref):
                self.assertTrue((SKILL / ref.rstrip(".,")).exists(), ref)

    def test_no_pipeline_only_references(self):
        for pattern in PIPELINE_ONLY:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.raw, re.I),
                                  f"SKILL.md mentions pipeline-only thing: {pattern}")

    def test_script_is_stdlib_only_and_offline(self):
        tree = ast.parse(read(SCRIPT))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertLessEqual(imported, {"__future__", "argparse", "json", "re", "sys", "pathlib"})

    def test_framing_sentence_in_skill_md_and_readme(self):
        for label, text in (("SKILL.md", self.body), ("README.md", read(README))):
            flat = " ".join(text.split())
            for pattern, what in FRAMING:
                with self.subTest(file=label, claim=what):
                    self.assertRegex(flat, re.compile(pattern, re.I))

    def test_skill_md_has_the_sections_a_single_agent_needs(self):
        for heading in ("## Method", "## Running the scan", "## Reading the rating",
                        "## What this is not"):
            self.assertIn(heading, self.body)

    def test_all_43_patterns_are_covered_by_number(self):
        # The condensed catalog in SKILL.md lists every pattern as "**NN Name**",
        # in order, once each, so the numbers match patterns.json.
        listed = [int(n) for n in re.findall(r"(?m)^- \*\*(\d{2}) ", self.body)]
        self.assertEqual(listed, list(range(1, 44)))
        catalog = json.loads(read(PATTERNS))["signs_of_ai_writing_catalog"]
        in_json = sorted(int(k[:2]) for b, v in catalog.items()
                         if not b.startswith("_") and isinstance(v, dict)
                         for k in v if re.match(r"^\d{2}_", k))
        self.assertEqual(listed, in_json)


class TestRepoFiles(unittest.TestCase):
    def test_readme(self):
        text = read(README)
        self.assertGreaterEqual(len(text.split()), 40)
        self.assertIn("npx skills add indranilbanerjee/contentforge-humanizer", text)
        self.assertIn("https://github.com/indranilbanerjee/contentforge", text)
        self.assertIn("skills/humanizer", text)

    def test_license_and_gitignore(self):
        lic = read(ROOT / "LICENSE")
        self.assertIn("MIT License", lic)
        self.assertIn("Copyright (c) 2026 Indranil Banerjee", lic)
        self.assertTrue((ROOT / ".gitignore").is_file())

    def test_readme_example_is_a_real_run(self):
        text = read(README)
        draft = re.search(r"```text\n(.*?)\n```", text, re.S)
        output = re.search(r"```json\n(.*?)\n```", text, re.S)
        self.assertTrue(draft and output, "README needs a ```text draft and a ```json output block")
        self.assertEqual(json.loads(output.group(1)), hero.ai_tell_scan(draft.group(1)))


# ---------------------------------------------------------------------------
# 4. Parity with ContentForge (skipped when it is not alongside)
# ---------------------------------------------------------------------------

def _function(path, name):
    tree = ast.parse(read(path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} not found in {path}")


def _assignment(path, name):
    tree = ast.parse(read(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node
    raise AssertionError(f"{name} not found in {path}")


def _code_dump(node):
    """ast.dump with docstrings removed: logic must match, prose may not."""
    node = copy.deepcopy(node)
    for n in ast.walk(node):
        if isinstance(n, ast.FunctionDef) and n.body:
            first = n.body[0]
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                n.body = n.body[1:] or [ast.Pass()]
    return ast.dump(node)


@unittest.skipUnless(HAVE_CF, "ContentForge not found alongside this repo (../../ContentForge)")
class TestParityWithContentForge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cf = load_module("cf_text_metrics", CF_TEXT_METRICS)

    @staticmethod
    def corpus():
        texts = {"fixture:ai_sounding": AI_SOUNDING, "fixture:human_plain": HUMAN_PLAIN,
                 "fixture:empty": EMPTY}
        texts.update({f"extra:{k}": v for k, v in EXTRA_PARITY_TEXTS.items()})
        docs = [CF_ROOT / "README.md", CF_ROOT / "CHANGELOG.md"]
        for sub in ("references", "agents"):
            docs += sorted((CF_ROOT / sub).glob("*.md"))
        for doc in docs:
            if doc.is_file():
                texts[f"cf:{doc.relative_to(CF_ROOT).as_posix()}"] = doc.read_text(
                    encoding="utf-8", errors="replace")
        return texts

    def test_scan_output_is_identical_on_fixtures_and_real_documents(self):
        texts = self.corpus()
        self.assertGreaterEqual(len(texts), 10)
        for name, text in texts.items():
            with self.subTest(text=name):
                self.assertEqual(hero.ai_tell_scan(text), self.cf.ai_tell_scan(text))

    def test_scan_output_is_identical_serialised(self):
        # Values AND key order, as printed.
        for name, text in self.corpus().items():
            with self.subTest(text=name):
                self.assertEqual(json.dumps(hero.ai_tell_scan(text), ensure_ascii=False),
                                 json.dumps(self.cf.ai_tell_scan(text), ensure_ascii=False))

    def test_cli_matches_text_metrics_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in (("ai", AI_SOUNDING), ("human", HUMAN_PLAIN), ("empty", EMPTY)):
                f = Path(tmp) / f"{name}.md"
                f.write_bytes(text.encode("utf-8"))
                with self.subTest(fixture=name):
                    code_h, out_h, _ = run_cli([str(f)], cwd=tmp)
                    code_c, out_c, _ = run_cli(["--file", str(f), "--ai-tell-scan"],
                                               cwd=tmp, script=CF_TEXT_METRICS)
                    self.assertEqual((code_h, code_c), (0, 0))
                    self.assertEqual(json.loads(out_h), json.loads(out_c)["ai_tell_scan"])

    def test_scan_code_is_the_same_code(self):
        for name in ("split_sentences", "is_aphorism_candidate", "ai_tell_scan"):
            with self.subTest(function=name):
                self.assertEqual(_code_dump(_function(SCRIPT, name)),
                                 _code_dump(_function(CF_TEXT_METRICS, name)))
        self.assertEqual(ast.dump(_assignment(SCRIPT, "_PRONOUN_RE")),
                         ast.dump(_assignment(CF_TEXT_METRICS, "_PRONOUN_RE")))

    def test_thresholds_match_contentforge(self):
        cf_thr = json.loads(read(CF_THRESHOLDS))["default"]["quality_gates"][
            "phase_6_5_humanizer"]["ai_tell_scan"]
        self.assertEqual(hero.THRESHOLDS, cf_thr)

    def test_patterns_json_is_a_verbatim_copy(self):
        # Line endings may differ between a Windows working copy and a clone;
        # content may not.
        self.assertEqual(norm_eol(PATTERNS.read_bytes()), norm_eol(CF_PATTERNS.read_bytes()))

    def test_reference_is_a_verbatim_copy(self):
        self.assertEqual(norm_eol(REFERENCE.read_bytes()), norm_eol(CF_REFERENCE.read_bytes()))


if __name__ == "__main__":
    unittest.main()
