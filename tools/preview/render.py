"""Turn tokenizer output into HTML.

Every scoped token carries `data-scope` with its full scope name, which is what
the page's hover readout displays.
"""
import html
import os

from tmtokenize import Grammar, tokenize

# Longest prefix first: cls() returns the first entry that matches.
CLS = [
    ("keyword.other.documentation",      "doctag"),
    ("entity.name.type.documentation",   "doctype"),
    ("variable.parameter.documentation", "docparam"),
    ("comment",                          "comment"),
    ("string",                           "string"),
    ("constant.character",               "char"),
    ("constant.numeric",                 "number"),
    ("constant.other.symbol",            "symbol"),
    ("constant.language",                "const"),
    ("entity.name.function",             "function"),
    ("entity.name.type",                 "type"),
    ("entity.name.label",                "label"),
    ("storage.type.class",               "type"),
    ("storage.type",                     "storage"),
    ("storage.modifier",                 "storage"),
    ("keyword.operator",                 "operator"),
    ("keyword.control",                  "keyword"),
    ("keyword.other",                    "keyword"),
    ("variable.other.global",            "globalref"),
    ("variable.language.global",         "sysglobal"),
    ("variable.language",                "varlang"),
    ("variable.other.property",          "property"),
]


def cls(scope):
    if not scope:
        return "plain"
    for prefix, name in CLS:
        if scope.startswith(prefix):
            return name
    return "plain"


def _lines(code, grammar):
    lines, cur = [], []
    for text, scope in tokenize(grammar, code.rstrip("\n")):
        if text == "\n":
            lines.append("".join(cur))
            cur = []
        elif text:
            attr = f' data-scope="{html.escape(scope, quote=True)}"' if scope else ""
            cur.append(f'<span class="t-{cls(scope)}"{attr}>{html.escape(text)}</span>')
    if cur:
        lines.append("".join(cur))
    return lines


def block(code, grammar):
    """A highlighted code block without line numbers."""
    return f'<pre class="code"><code>{chr(10).join(_lines(code, grammar))}</code></pre>'


def filepane(path, grammar):
    """A whole file: scrollable, line numbered."""
    lines = _lines(open(path, encoding="utf8").read(), grammar)
    # no placeholder on blank lines: the line-number pseudo-element keeps the
    # box open, and a &nbsp; would end up in anything copied out of the page
    body = "".join(f'<span class="line">{l}</span>' for l in lines)
    name = os.path.basename(path)
    return (f'<figure class="pane">'
            f'<figcaption><span class="dot"></span>{html.escape(name)}'
            f'<span class="lc">{len(lines)} lines</span></figcaption>'
            f'<pre><code>{body}</code></pre></figure>')
