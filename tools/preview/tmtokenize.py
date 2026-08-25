"""A minimal TextMate tokenizer.

Implements the resolution rules the real engines use, which is what makes the
preview trustworthy: the leftmost match wins, ties are broken by the order rules
appear in the include list, and begin/end rules are held on a stack so their
`patterns` replace the enclosing set while they are open.

This is a faithful subset, not vscode-textmate. It has no injections, no
backreferenced end patterns and no `while` rules -- none of which this grammar
uses. Patterns are compiled with Python's `re`, so a construct PCRE or Oniguruma
accepts but Python does not (multi-length lookbehind, for one) will raise here.
"""
import json
import re


def rx(pattern):
    flags = re.M
    if pattern.startswith("(?i)"):
        pattern, flags = pattern[4:], flags | re.I
    return re.compile(pattern, flags)


class Grammar:
    def __init__(self, path):
        data = json.load(open(path, encoding="utf8"))
        self.repo = data["repository"]
        self.top = self.resolve(data["patterns"])

    def resolve(self, patterns):
        """Flatten #include references into a plain list of rules."""
        out = []
        for p in patterns:
            if "include" in p:
                inc = p["include"]
                if inc in ("$self", "$base"):
                    # kept as a marker; expanded by the caller against the root
                    out.append(p)
                    continue
                key = inc.lstrip("#")
                if key in self.repo:
                    out.extend(self.resolve(self.repo[key].get("patterns", [])))
            else:
                out.append(p)
        return out

    def compile(self, patterns):
        compiled = []
        for p in patterns:
            if "match" in p:
                compiled.append(("m", rx(p["match"]), p))
            elif "begin" in p:
                compiled.append(("b", rx(p["begin"]), p))
        return compiled


def tokenize(grammar, text):
    """Yield (text, scope) pairs. Scope is None where nothing matched.

    Line breaks are emitted as ("\\n", None) so callers can rebuild lines.
    """
    # frame: (scope, patterns, end_rx, while_rx)
    stack = [(None, grammar.compile(grammar.top), None, None)]
    out = []
    for line in text.split("\n"):
        # a begin/while rule survives onto this line only while its pattern
        # still matches; when it stops, it and anything above it close
        drop = None
        for i, frame in enumerate(stack):
            wr = frame[3]
            if wr is not None and not wr.match(line):
                drop = i
                break
        if drop is not None:
            del stack[drop:]
        pos, end = 0, len(line)
        while pos <= end:
            scope, patterns, end_rx, _ = stack[-1]
            best = None
            # an open begin/end rule tries its end pattern first, at equal offset
            if end_rx is not None:
                m = end_rx.search(line, pos)
                if m:
                    best = (m.start(), 0, "e", m, None)
            for i, (kind, regex, rule) in enumerate(patterns):
                m = regex.search(line, pos)
                if m and (best is None or (m.start(), i + 1) < (best[0], best[1])):
                    best = (m.start(), i + 1, kind, m, rule)
            if best is None:
                if pos < end:
                    out.append((line[pos:], scope))
                break
            start, _, kind, m, rule = best
            if start > pos:
                out.append((line[pos:start], scope))

            def emit_captures(captures, fallback):
                last = m.start()
                for gi in sorted(int(k) for k in captures):
                    if gi == 0 or m.group(gi) is None:
                        continue
                    gs, ge = m.span(gi)
                    if gs > last:
                        out.append((line[last:gs], fallback))
                    cap = captures[str(gi)]
                    if "patterns" in cap:
                        sub = Grammar.__new__(Grammar)
                        sub.repo = grammar.repo
                        expanded = []
                        for entry in grammar.resolve(cap["patterns"]):
                            if entry.get("include") in ("$self", "$base"):
                                expanded.extend(grammar.top)
                            else:
                                expanded.append(entry)
                        sub.top = expanded
                        for tt, ss in tokenize(sub, m.group(gi)):
                            if tt != "\n":
                                out.append((tt, ss if ss else cap.get("name")))
                    else:
                        out.append((m.group(gi), cap.get("name")))
                    last = ge
                if last < m.end():
                    out.append((line[last:m.end()], fallback))

            if kind == "e":
                out.append((m.group(0), scope))
                stack.pop()
            elif kind == "m":
                caps = rule.get("captures")
                if caps and m.lastindex:
                    emit_captures(caps, rule.get("name") or scope)
                else:
                    out.append((m.group(0), rule.get("name") or scope))
            else:
                name = rule.get("name") or scope
                caps = rule.get("beginCaptures")
                if caps and m.lastindex:
                    emit_captures(caps, name)
                else:
                    out.append((m.group(0), name))
                inner = grammar.compile(grammar.resolve(rule.get("patterns", [])))
                content = rule.get("contentName") or name
                if "while" in rule:
                    stack.append((content, inner, None, rx(rule["while"])))
                else:
                    stack.append((content, inner, rx(rule["end"]), None))
            # never let a zero-width match stall the scan
            pos = m.end() if m.end() > m.start() else m.start() + 1
        # rules that end at "$" close with the line
        while len(stack) > 1 and stack[-1][2] is not None and stack[-1][2].pattern == "$":
            stack.pop()
        out.append(("\n", None))
    return out
