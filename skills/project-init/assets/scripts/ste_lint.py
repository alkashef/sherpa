"""Lint the docs that a person reads for ASD-STE100 Simplified Technical English, flavored mode.

For each file it counts the marks of text that is hard to read: sentences over 20 words,
semicolons, contractions, passive voice, perfect tenses, `be` + `-ing` verbs, nominalizations,
phrasal verbs, banned and marketing words, hedges, and paragraphs over 6 sentences. The score is
the count for each 100 words. Code (fenced blocks and `inline code`) does not count.

    python scripts/ste_lint.py README.md CLAUDE.md docs/*.md
    python scripts/ste_lint.py --fail-over 2.5 --min-words 100 --repeated 12 README.md docs/*.md

--fail-over N exits 1 when a file scores over N. --min-words N skips a file of fewer words.
--repeated N exits 1 when a sentence of N words or more is in two files: a fact belongs in one
place. --repeated-skip FILE leaves a file out of that check. `scripts/check.py` runs it on
README.md, CLAUDE.md and docs/*.md, and leaves CLAUDE.md out of the check of repeated sentences:
its Project section repeats the purpose of README.md on purpose, for each session of Claude. EARS
keeps "shall": the flavored mode allows it.

The rules and the score come from ste-lint.py of the asd-ste100 skill (score version 2). One
change: a list item is a paragraph of its own, and a table row is in no paragraph, so a long list
or table does not count as a long paragraph. The license of ste-lint.py:

    MIT License

    Copyright (c) 2026 Ege Chelebi

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software
    and associated documentation files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or
    substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
    BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

ASD-STE100 is a registered EU trademark (No. 017966390) of ASD. This script is unofficial and not
affiliated with ASD. The license above does not cover the ASD-STE100 specification.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MARKETING = [
    "seamless",
    "seamlessly",
    "robust",
    "powerful",
    "cutting-edge",
    "effortless",
    "effortlessly",
    "world-class",
    "next-generation",
    "revolutionary",
    "blazing",
    "lightning-fast",
    "elegant",
    "delightful",
    "turnkey",
    "best-in-class",
    "state-of-the-art",
    "game-changing",
    "first-class",
    "battle-tested",
    "enterprise-grade",
    "supercharge",
    "unlock",
    "unleash",
    "empower",
    "empowers",
]
BANNED = [
    *[
        "begin",
        "begins",
        "commence",
        "commences",
        "initiate",
        "initiates",
        "originate",
        "utilize",
        "utilizes",
        "utilizing",
        "leverage",
        "leverages",
        "leveraging",
        "facilitate",
        "facilitates",
        "ensure",
        "ensures",
        "ensuring",
        "obtain",
        "obtains",
        "acquire",
        "acquires",
        "demonstrate",
        "demonstrates",
        "additionally",
        "furthermore",
        "moreover",
        "comprehensive",
        "comprehensively",
        "utilization",
        "aforementioned",
        "henceforth",
        "therein",
        "whilst",
        "amongst",
        "numerous",
        "myriad",
        "plethora",
        "provide",
        "provides",
        "provided",
    ],
    "prior to",
    "subsequent to",
    "in order to",
    "a variety of",
    "in the event that",
    "due to the fact that",
    "it is important to note",
]
PHRASAL = [
    "spin up",
    "spin down",
    "reach out",
    "dive into",
    "dives into",
    "diving into",
    "kick off",
    "kicks off",
    "roll out",
    "rolls out",
    "tear down",
    "ramp up",
    "circle back",
    "drill down",
    "spun up",
    "reaching out",
]
MODAL_HEDGE = [
    "it is important to note",
    "it should be noted",
    "it is worth noting",
    "please note that",
    "as mentioned",
    "as noted above",
]
BE = r"(?:am|is|are|was|were|be|been|being)"
IRREGULAR = (
    r"(?:done|made|sent|read|built|kept|held|set|put|run|written|shown|given|taken|found|got"
    r"|gotten|seen|known|thrown|drawn)"
)
# A past participle used as an adjective is not passive, unless a by-agent follows.
STATIVE = (
    r"(?:closed|opened?|damaged|completed?|installed|connected|required|expected|configured"
    r"|enabled|disabled|deprecated|supported)"
)
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
LONG_SENTENCE = 20
LONG_PARAGRAPH = 6
FAILED = 1


@dataclass(frozen=True)
class Score:
    """The marks of one text: how many words, how many marks, and the marks for 100 words."""

    words: int
    total: int

    @property
    def per_100_words(self) -> float:
        """Return the marks for each 100 words, rounded to two places."""
        return round(self.total * 100.0 / max(self.words, 1), 2)


def strip_code(text: str) -> str:
    """Return the text without fenced code blocks and inline code."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", " ", text)


def paragraphs(raw: str) -> list[str]:
    """Return the paragraphs of a text, after the fenced code blocks are gone.

    Each list item is a paragraph of its own, and a table row is in no paragraph: the style asks
    for lists and tables before prose, so a long list or table is not a long paragraph.
    """
    text = re.sub(r"```.*?```", "\n\n", raw, flags=re.DOTALL)
    text = re.sub(r"^[ \t]*```.*$", "\n", text, flags=re.MULTILINE)
    text = re.sub(r"`[^`]*`", " ", text)
    found: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        current: list[str] = []
        for line in block.split("\n"):
            if line.lstrip().startswith("|"):
                continue
            if LIST_ITEM.match(line) and current:
                found.append("\n".join(current))
                current = []
            current.append(line)
        found.append("\n".join(current))
    return [part for part in found if part.strip()]


def sentences(text: str) -> list[str]:
    """Return the sentences of a text: each line without its heading or list mark, then split."""
    found: list[str] = []
    for line in text.split("\n"):
        stripped = re.sub(r"^\s*#{1,6}\s*", "", line.strip())
        stripped = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", stripped)
        parts = re.split(r"(?<=[.!?:])\s+(?=[A-Z0-9\"'\-])", stripped) if stripped else []
        found += [part.strip() for part in parts if part.strip()]
    return found


def word_count(sentence: str) -> int:
    """Return the number of words in a sentence."""
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-/]*", sentence))


def count_phrases(text: str, phrases: list[str]) -> int:
    """Return how many times the phrases occur in the text, as whole words, in any case."""
    low = text.lower()
    return sum(
        len(re.findall(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", low)) for phrase in phrases
    )


def grammar_marks(text: str) -> int:
    """Return the marks of passive voice, perfect tenses, `be` + `-ing` and nominalizations."""
    passive = re.findall(rf"\b{BE}\s+(\w+ed|{IRREGULAR})\b", text, re.IGNORECASE)
    marks = sum(1 for word in passive if not re.fullmatch(STATIVE, word, re.IGNORECASE))
    marks += len(re.findall(rf"\b{BE}\s+{STATIVE}\s+by\b", text, re.IGNORECASE))
    modal = r"(?:may|might|could|would|should|must|will|shall|can)"
    perfect = rf"\b(?:{modal}\s+)?(?:have|has|had)\s+(?:been\s+)?(?:\w+ed|{IRREGULAR})\b"
    marks += len(re.findall(perfect, text, re.IGNORECASE))
    marks += len(re.findall(rf"\b{BE}\s+\w+ing\b", text, re.IGNORECASE))
    verbs = (
        r"\b(?:perform(?:s|ed)?|conduct(?:s|ed)?|carry out|carries out|make use of|makes use of)\b"
    )
    marks += len(re.findall(verbs, text, re.IGNORECASE))
    return marks + len(re.findall(r"\b\w{4,}(?:tion|ment|ance|ence)\s+of\b", text, re.IGNORECASE))


def lint(raw: str) -> Score:
    """Return the score of a text, in flavored mode."""
    text = strip_code(raw)
    found = sentences(text)
    words = sum(word_count(sentence) for sentence in found) or 1
    total = sum(1 for sentence in found if word_count(sentence) > LONG_SENTENCE)
    total += text.count(";")
    total += len(re.findall(r"\b\w+['\u2019](?:t|re|ve|ll|d|s|m)\b", text))
    total += grammar_marks(text)
    for phrases in (PHRASAL, BANNED, MARKETING, MODAL_HEDGE):
        total += count_phrases(text, phrases)
    total += sum(1 for part in paragraphs(raw) if len(sentences(part)) > LONG_PARAGRAPH)
    return Score(words, total)


def normalized(sentence: str) -> str:
    """Return a sentence in lower case, without Markdown marks and extra spaces."""
    text = re.sub(r"[*_`|>]", " ", sentence.lower())
    return " ".join(text.split()).rstrip(".:")


def repeated_sentences(texts: dict[str, str], min_words: int) -> list[str]:
    """Return one message for each sentence of min_words words or more that two files hold.

    A table row is data, not a sentence, so it does not count.
    """
    first_seen: dict[str, str] = {}
    problems: list[str] = []
    for name, raw in texts.items():
        prose = re.sub(r"```.*?```", " ", raw, flags=re.DOTALL)
        lines = [line for line in prose.split("\n") if not line.lstrip().startswith("|")]
        for sentence in dict.fromkeys(sentences("\n".join(lines))):
            key = normalized(sentence)
            if word_count(key) < min_words:
                continue
            where = first_seen.setdefault(key, name)
            if where != name:
                problems.append(f'"{sentence[:70]}..." is in {where} and {name}. Keep it in one.')
    return problems


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command line."""
    parser = argparse.ArgumentParser(description="Lint docs for Simplified Technical English.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--fail-over", type=float, default=None, help="exit 1 over this score")
    parser.add_argument("--min-words", type=int, default=0, help="skip a shorter file")
    parser.add_argument("--repeated", type=int, default=0, help="exit 1 on a repeated sentence")
    parser.add_argument(
        "--repeated-skip",
        action="append",
        default=[],
        type=Path,
        help="a file that the check of repeated sentences leaves out (give it again for more)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Print the score of each file, and each repeated sentence. Return 1 when a limit fails."""
    args = parse_args(argv)
    texts = {path.as_posix(): path.read_text(encoding="utf-8") for path in args.files}
    failed = False
    for name, raw in texts.items():
        score = lint(raw)
        skipped = score.words < args.min_words
        over = args.fail_over is not None and score.per_100_words > args.fail_over and not skipped
        state = "skipped" if skipped else "over" if over else "ok"
        sys.stdout.write(f"{name}: {score.words} words, {score.per_100_words} for 100 ({state})\n")
        failed = failed or over
    skipped_names = {path.as_posix() for path in args.repeated_skip}
    compared = {name: raw for name, raw in texts.items() if name not in skipped_names}
    problems = repeated_sentences(compared, args.repeated) if args.repeated else []
    for problem in problems:
        sys.stdout.write(f"{problem}\n")
    return FAILED if failed or problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
