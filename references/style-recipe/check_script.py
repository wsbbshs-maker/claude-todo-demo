#!/usr/bin/env python3
"""Check a narration script against the measured reference formula.

  python3 check_script.py script.txt [--seconds 67]

Formula (20/20 reference videos): hook = paradox stated as fact in sentence 1 (~10-16 words);
setting in 1-2 present-tense lines; escalation with short dialogue; ~1 mystery beat
("Wait, ...?" / a question); pivot "You see," (14/20) -> mechanism, often an everyday analogy;
ironic payoff in the last 1-2 short sentences; median sentence ~13.5 words; contractions;
pace 3.5-4.1 words/s (median 3.7).
"""
import argparse
import re
import statistics

CONTRACTION = re.compile(r"\b\w+'(s|re|ve|ll|d|t|m)\b", re.I)
ANALOGY = re.compile(r"\b(ever |think about|picture |imagine |like when|it's like)\b", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--seconds", type=float, default=None, help="planned video length")
    a = ap.parse_args()
    text = open(a.path, encoding="utf-8").read().replace("’", "'")
    text = re.sub(r"\s+", " ", text).strip()
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[\"'A-Z])", text) if s.strip()]
    words = re.findall(r"[A-Za-z0-9']+", text)
    wc = len(words)
    lens = [len(re.findall(r"[A-Za-z0-9']+", s)) for s in sents]

    rows = []
    def row(name, value, ok, target):
        rows.append((name, value, "ok" if ok else "CHECK", target))

    row("words", wc, True, "")
    for wps in (3.5, 3.7, 4.1):
        rows.append((f"duration @ {wps} w/s", f"{wc / wps:.1f} s", "", ""))
    if a.seconds:
        need = a.seconds * 3.7
        row("words for planned length", f"{need:.0f}", abs(wc - need) / need < 0.08, "+-8 % of 3.7 w/s")
    med = statistics.median(lens)
    row("median sentence length", f"{med:.1f}", 11 <= med <= 16, "~13.5 words")
    row("hook (sentence 1) length", lens[0], 10 <= lens[0] <= 16, "10-16 words, paradox as fact")
    pivot = [i for i, s in enumerate(sents) if s.lower().startswith("you see")]
    row("pivot 'You see,'", f"sentence {pivot[0] + 1}/{len(sents)}" if pivot else "missing",
        bool(pivot) and 0.45 <= pivot[0] / len(sents) <= 0.85, "in the 2nd half, before the mechanism")
    q = [i for i, s in enumerate(sents) if s.endswith("?") or s.lower().startswith("wait")]
    row("mystery beat (? / Wait,)", len(q), len(q) >= 1, ">= 1")
    row("everyday analogy", len(ANALOGY.findall(text)), bool(ANALOGY.search(text)), "'Ever ...?', 'picture ...', 'think about ...'")
    dialog = len(re.findall(r"[\"“][^\"”]{2,80}[\"”]", text))
    row("dialogue lines", dialog, dialog >= 2, "short in-character lines during escalation")
    row("contractions", len(CONTRACTION.findall(text)), len(CONTRACTION.findall(text)) >= wc / 40, ">= 1 per ~40 words")
    tail = lens[-1]
    row("last sentence length", tail, tail <= 12, "short ironic payoff, video ends on it")
    long = [l for l in lens if l > 25]
    row("sentences > 25 words", len(long), not long, "split them")

    w = max(len(r[0]) for r in rows)
    for name, value, verdict, target in rows:
        print(f"{name:{w}s}  {str(value):>14s}  {verdict:5s}  {target}")


if __name__ == "__main__":
    main()
