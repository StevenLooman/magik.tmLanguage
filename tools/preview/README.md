# Syntax highlighting preview

Renders `grammars/magik.tmLanguage.json` over sample Magik and writes a
self-contained HTML page. Every token carries its scope name, and hovering one
shows that scope in a bar at the bottom of the page — useful for checking what a
rule actually produces rather than what it looks like it should produce.

## Usage

From the Linguist checkout that vendors this grammar:

```sh
python3 vendor/grammars/magik.tmLanguage/tools/preview/build.py
```

Standalone, from a clone of this repository on its own:

```sh
python3 tools/preview/build.py
```

The page is built from `tour.magik` here in the repository, which is enough on
its own. Pass `--samples` a directory of `.magik` files to render those in full
beneath the scope map as well — Linguist's `samples/Magik`, say, when this
grammar is vendored there, or any checkout you have to hand. Nothing is bundled
for this: a corpus worth auditing is one written by somebody who had never seen
this grammar, which rules out anything shipped alongside it.

Options: `--grammar` (defaults to this repo's grammar), `--samples`, `--out`
(defaults to `preview.html` beside the script). No dependencies beyond the
standard library.

## Files

| file | purpose |
|---|---|
| `tmtokenize.py` | a minimal TextMate tokenizer |
| `render.py` | tokens to HTML, scope name to CSS class |
| `tour.magik` | a short sample covering every construct the grammar distinguishes |
| `build.py` | assembles the page |
| `audit.py` | tokenizes a corpus and reports signs the grammar is wrong |

## What the tokenizer does and does not do

It implements the resolution rules that decide most real highlighting bugs:

- the **leftmost** match wins, regardless of rule order;
- at an **equal offset**, the rule listed first in `patterns` wins;
- `begin`/`end` rules are pushed on a stack, and their `patterns` **replace** the
  enclosing set while open.

That last two are worth stressing. Several bugs in this grammar were pure
ordering problems, invisible from reading the regexes alone: a rule that matched
correctly but was listed after one that matched at the same offset, and a
`begin`/`end` rule whose inner set was missing everything it needed.

It is a faithful subset, not `vscode-textmate`. There are no injections, no
backreferenced end patterns and no `while` rules — none of which this grammar
uses. Patterns compile with Python's `re`, so a construct PCRE and Oniguruma
accept but Python does not — a multi-length lookbehind such as
`(?<=_leave|_continue)` — raises here. That is a useful constraint: writing the
lookbehinds as separate fixed-width alternatives keeps the grammar portable
across all three engines.

Treat the output as a close preview rather than a byte-for-byte guarantee.
GitHub applies its own theme; the colours here are illustrative.

## Auditing a corpus

`build.py` shows what the grammar does to code you chose. `audit.py` points it
at code you did not:

```sh
python3 tools/preview/audit.py /path/to/some/magik/checkout
```

It reports, and exits non-zero on, five things:

1. **Identifiers split across scopes** — two adjacent tokens with different
   scopes whose touching characters are both identifier characters. One name has
   been cut in two. This is what a keyword pattern missing its word boundary
   looks like, and it is how `stub_proc_helper` was found tokenised as
   `stub` + `_proc` + `_helper`.
2. **Unscoped underscore words** — every Magik keyword starts with `_`, so an
   unscoped one suggests a rule that does not exist yet.
3. **Unscoped literals** — a bare `:symbol` or `%char` no rule claimed.
4. **Strings open at the end of a line** — a begin/end rule running away.
5. **Method definitions not recognised** at all.

None of these prove a bug; they are places to look. Two of the five produced
false positives when first written — consecutive `##` lines read as one long
comment, and every closed string read as open because its closing quote carries
the string scope too. Check a finding before believing it.

A corpus of roughly 1.7 MB across ten Smallworld repositories currently reports
nothing. That is only meaningful because the check has been shown to fire: run
it against a grammar with `\b` removed from `_proc` and it reports the split
immediately.
