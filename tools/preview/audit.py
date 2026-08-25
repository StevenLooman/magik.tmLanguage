#!/usr/bin/env python3
"""Tokenize a corpus of Magik and report signs the grammar is wrong.

    python3 tools/preview/audit.py DIR [DIR...]

Checks, in rough order of how much they have caught:

1. Identifiers split across scopes. If two adjacent tokens carry different
   scopes but their touching characters are both identifier characters, one name
   has been cut in two. This is what a keyword pattern missing its word boundary
   looks like: `stub_proc_helper` tokenised as `stub` + `_proc` + `_helper`.
2. Underscore words left unscoped. Every Magik keyword starts with `_`, so an
   unscoped one is a candidate for a rule that does not exist yet.
3. Literals left unscoped -- a bare `:symbol` or `%char` that no rule claimed.
4. Strings still open at the end of a line, which means a begin/end rule is
   running away.
5. Method definitions the grammar fails to recognise at all.

None of these prove a bug on their own; they are places to look.
"""
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tmtokenize import Grammar, tokenize   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GRAMMAR = os.path.join(HERE, "..", "..", "grammars", "magik.tmLanguage.json")
IDENT = re.compile(r"[A-Za-z0-9_!?]")
METHOD_LINE = re.compile(r"\s*(?:_(?:private|iter|abstract)\s+)*_method\b", re.I)


def main(roots):
    grammar = Grammar(GRAMMAR)
    splits = collections.Counter()
    kw = collections.Counter()
    lits = collections.Counter()
    open_strings, missed = [], []
    files = tokens = 0

    for root in roots:
        for path in sorted(glob.glob(os.path.join(root, "**", "*.magik"), recursive=True)):
            files += 1
            src = open(path, encoding="utf8", errors="replace").read()
            toks = tokenize(grammar, src)
            tokens += len(toks)

            line, lineno = [], 1
            for text, scope in toks:
                if text != "\n":
                    line.append((text, scope))
                    continue
                for i in range(len(line) - 1):
                    (t1, s1), (t2, s2) = line[i], line[i + 1]
                    if t1 and t2 and s1 != s2 and IDENT.match(t1[-1]) and IDENT.match(t2[0]):
                        splits[(t1[-14:], s1, t2[:14], s2)] += 1
                for text2, scope2 in line:
                    if scope2 is None:
                        kw.update(re.findall(r"(?<![A-Za-z0-9_!?])_[a-z][a-z0-9_]*", text2))
                        lits.update(re.findall(r"(?<![A-Za-z0-9_!?]):[A-Za-z0-9_!?]+|%\w+", text2))
                # a string is still open only if its last token is not the
                # closing quote -- the closing quote carries the string scope
                # too, so "last token is a string" flags every closed one
                str_toks = [t for t, sc in line if sc and sc.startswith("string")]
                if str_toks and str_toks[-1] not in ('"', "'"):
                    open_strings.append(f"{path}:{lineno}")
                line, lineno = [], lineno + 1

            for i, text in enumerate(src.split("\n"), 1):
                if METHOD_LINE.match(text):
                    if not any(s == "storage.type.function.magik"
                               for _, s in tokenize(grammar, text)):
                        missed.append(f"{path}:{i}: {text.strip()[:80]}")

    print(f"files: {files}   tokens: {tokens:,}")
    report("identifiers split across scopes", splits, fmt=lambda k:
           f"{k[0]!r}[{(k[1] or '-').replace('.magik','')}]"
           f" + {k[2]!r}[{(k[3] or '-').replace('.magik','')}]")
    report("unscoped underscore words", kw)
    report("unscoped literals", lits)
    report("strings open at end of line", collections.Counter(open_strings))
    report("method definitions not recognised", collections.Counter(missed))
    total = sum(map(sum, (c.values() for c in (splits, kw, lits))))
    total += len(open_strings) + len(missed)
    print(f"\n{'no findings' if total == 0 else str(total) + ' finding(s)'}")
    return 1 if total else 0


def report(title, counter, fmt=str, limit=12):
    print(f"\n{title}: {sum(counter.values())}")
    for key, n in counter.most_common(limit):
        print(f"   {n:>5}  {fmt(key)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
