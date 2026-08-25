#!/usr/bin/env python3
"""Build the Magik syntax-highlighting preview page.

    python3 tools/preview/build.py [--samples DIR] [--out FILE]

Defaults assume this grammar is vendored as a Linguist submodule, so samples are
found at ../../../samples/Magik relative to the repository root.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from tmtokenize import Grammar          # noqa: E402
from render import block, filepane      # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_GRAMMAR = os.path.join(REPO, "grammars", "magik.tmLanguage.json")
DEFAULT_SAMPLES = os.path.join(REPO, "samples")

TOKENS = [
    ("keyword",     "keyword.control / keyword.other"),
    ("storage",     "storage.type / storage.modifier"),
    ("type",        "entity.name.type.class"),
    ("function",    "entity.name.function"),
    ("property",    "variable.other.property (slot)"),
    ("varlang",     "variable.language (_self, _clone)"),
    ("sysglobal",   "variable.language.global (!name!)"),
    ("globalref",   "variable.other.global (@name)"),
    ("label",       "entity.name.label"),
    ("symbol",      "constant.other.symbol"),
    ("const",       "constant.language"),
    ("number",      "constant.numeric"),
    ("string",      "string.quoted"),
    ("char",        "constant.character"),
    ("operator",    "keyword.operator"),
    ("comment",     "comment"),
    ("doctag",      "keyword.other.documentation"),
    ("doctype",     "entity.name.type.documentation"),
    ("docparam",    "variable.parameter.documentation"),
]

CSS = """
:root{
  --bg:#F4F6F9; --surface:#FFFFFF; --surface-2:#FBFCFD;
  --ink:#141C25; --ink-2:#41505F; --muted:#6B7A8A;
  --rule:#DCE3EB; --rule-2:#EAEFF4;
  --accent:#005CB9; --accent-soft:#E4EEF9;
  --t-plain:#2B3946; --t-comment:#6E8091; --t-string:#9A5B2E; --t-number:#2C6E5A;
  --t-symbol:#7A3FA8; --t-const:#005CB9; --t-function:#8A5A00; --t-type:#0D6C6C;
  --t-label:#C1440E; --t-storage:#005CB9; --t-operator:#5A6875;
  --t-keyword:#9B2E86; --t-sysglobal:#8A5A00; --t-varlang:#005CB9; --t-property:#2F6FA8;
  --t-globalref:#0E7C6B;
  --t-doctag:#3F6E99; --t-doctype:#2E8B72; --t-docparam:#9A4F91;
  --hi:rgba(0,92,185,.13);
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#0E141A; --surface:#151C24; --surface-2:#111820;
  --ink:#E6ECF2; --ink-2:#B3C0CC; --muted:#8494A3;
  --rule:#243039; --rule-2:#1C262E;
  --accent:#61A9EA; --accent-soft:#132534;
  --t-plain:#D3DCE5; --t-comment:#7E909F; --t-string:#D69B6B; --t-number:#84CBAE;
  --t-symbol:#C79BE8; --t-const:#61A9EA; --t-function:#E0C177; --t-type:#5FC6C6;
  --t-label:#FF9E7A; --t-storage:#61A9EA; --t-operator:#96A5B3;
  --t-keyword:#E08BCB; --t-sysglobal:#E0C177; --t-varlang:#61A9EA; --t-property:#8FBEE8;
  --t-globalref:#66D0BE;
  --t-doctag:#8FBEE8; --t-doctype:#77CEB4; --t-docparam:#DDA6D6;
  --hi:rgba(97,169,234,.18);
}}
:root[data-theme="dark"]{
  --bg:#0E141A; --surface:#151C24; --surface-2:#111820;
  --ink:#E6ECF2; --ink-2:#B3C0CC; --muted:#8494A3;
  --rule:#243039; --rule-2:#1C262E;
  --accent:#61A9EA; --accent-soft:#132534;
  --t-plain:#D3DCE5; --t-comment:#7E909F; --t-string:#D69B6B; --t-number:#84CBAE;
  --t-symbol:#C79BE8; --t-const:#61A9EA; --t-function:#E0C177; --t-type:#5FC6C6;
  --t-label:#FF9E7A; --t-storage:#61A9EA; --t-operator:#96A5B3;
  --t-keyword:#E08BCB; --t-sysglobal:#E0C177; --t-varlang:#61A9EA; --t-property:#8FBEE8;
  --t-globalref:#66D0BE;
  --t-doctag:#8FBEE8; --t-doctype:#77CEB4; --t-docparam:#DDA6D6;
  --hi:rgba(97,169,234,.18);
}
*{box-sizing:border-box}
body{margin:0; background:var(--bg); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif; font-size:16px; line-height:1.6;}
.wrap{max-width:1080px; margin:0 auto; padding:clamp(2rem,5vw,4rem) clamp(1rem,4vw,2.5rem) 6rem}
header{display:flex; flex-direction:column; gap:.85rem; padding-bottom:1.8rem; border-bottom:1px solid var(--rule)}
.eyebrow{font-family:"IBM Plex Mono",monospace; font-size:.72rem; font-weight:500; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent); display:flex; align-items:center; gap:.6rem}
.eyebrow .chip{width:.62rem;height:.62rem;border-radius:2px;background:#005CB9}
h1{font-family:"IBM Plex Serif",Georgia,serif; font-weight:600; font-size:clamp(1.9rem,4.4vw,2.8rem);
  line-height:1.12; margin:0; text-wrap:balance; letter-spacing:-.015em}
.lede{margin:0; max-width:64ch; color:var(--ink-2); font-size:1.05rem}
.meta{display:flex; flex-wrap:wrap; gap:.5rem; margin-top:.3rem}
.tag{font-family:"IBM Plex Mono",monospace; font-size:.73rem; color:var(--ink-2);
  border:1px solid var(--rule); border-radius:3px; padding:.24rem .55rem; background:var(--surface)}
section{padding-top:2.8rem}
h2{font-family:"IBM Plex Serif",Georgia,serif; font-weight:600; font-size:1.4rem; margin:0 0 .3rem;
  letter-spacing:-.01em; text-wrap:balance}
.why{margin:0 0 1.2rem; max-width:70ch; color:var(--ink-2)}
.why code,li code,.inline{font-family:"IBM Plex Mono",monospace; font-size:.88em;
  background:var(--rule-2); border-radius:3px; padding:.1rem .32rem; color:var(--ink)}
.hint{display:flex; align-items:center; gap:.5rem; margin:0 0 1rem; font-size:.85rem; color:var(--muted)}
.hint kbd{font-family:"IBM Plex Mono",monospace; font-size:.75rem; border:1px solid var(--rule);
  border-bottom-width:2px; border-radius:4px; padding:.1rem .4rem; background:var(--surface); color:var(--ink-2)}
pre.code, .pane{background:var(--surface); border:1px solid var(--rule); border-radius:6px; margin:0}
pre.code{padding:1rem; overflow-x:auto}
pre.code code, .pane code{font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.815rem;
  line-height:1.72; white-space:pre; tab-size:2; color:var(--t-plain)}
.legend{list-style:none; margin:1.2rem 0 0; padding:0; display:grid; gap:.3rem .9rem;
  grid-template-columns:repeat(auto-fill,minmax(255px,1fr))}
.legend li{display:flex; align-items:center; gap:.5rem; font-size:.8rem}
.legend .sw{font-size:.9rem; line-height:1}
.legend code{background:none; padding:0; color:var(--ink-2); font-size:.78rem}
.pane{overflow:hidden; margin-top:1rem}
.pane figcaption{display:flex; align-items:center; gap:.5rem; font-family:"IBM Plex Mono",monospace;
  font-size:.73rem; font-weight:500; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-2);
  padding:.55rem .85rem; border-bottom:1px solid var(--rule-2); background:var(--surface-2)}
.pane .dot{width:.5rem;height:.5rem;border-radius:50%;background:var(--accent)}
.pane .lc{margin-left:auto; opacity:.7; text-transform:none; letter-spacing:0}
.pane pre{margin:0; max-height:min(70vh,620px); overflow:auto; padding:.95rem 0}
.pane code{counter-reset:ln; display:block}
.line{display:block; counter-increment:ln; padding-right:1rem}
.line::before{content:counter(ln); display:inline-block; width:3.4em; margin-right:1.1em;
  text-align:right; color:var(--muted); opacity:.45; user-select:none; -webkit-user-select:none;
  font-variant-numeric:tabular-nums}
.files-nav{display:flex; flex-wrap:wrap; gap:.5rem; margin-bottom:.2rem}
.files-nav a{font-family:"IBM Plex Mono",monospace; font-size:.75rem; text-decoration:none;
  color:var(--accent); border:1px solid var(--rule); border-radius:3px; padding:.26rem .6rem;
  background:var(--surface)}
.files-nav a:hover,.files-nav a:focus-visible{background:var(--accent-soft)}
.open{list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:.85rem}
.open li{border-left:2px solid var(--rule); padding:.1rem 0 .1rem .9rem; max-width:72ch; color:var(--ink-2)}
.open b{color:var(--ink); font-weight:600}
[data-scope]{cursor:help; border-radius:2px}
[data-scope].is-hot{background:var(--hi)}
.t-plain{color:var(--t-plain)} .t-comment{color:var(--t-comment);font-style:italic}
.t-string{color:var(--t-string)} .t-char{color:var(--t-string);font-weight:600}
.t-number{color:var(--t-number)} .t-symbol{color:var(--t-symbol)} .t-const{color:var(--t-const)}
.t-function{color:var(--t-function)} .t-type{color:var(--t-type)}
.t-label{color:var(--t-label);text-decoration:underline;text-decoration-style:dotted;text-underline-offset:.18em}
.t-storage{color:var(--t-storage)} .t-operator{color:var(--t-operator)}
.t-keyword{color:var(--t-keyword)} .t-sysglobal{color:var(--t-sysglobal)}
.t-varlang{color:var(--t-varlang)} .t-property{color:var(--t-property)}
.t-globalref{color:var(--t-globalref);font-weight:500}

.t-doctag{color:var(--t-doctag);font-weight:600;font-style:normal}
.t-doctype{color:var(--t-doctype);font-style:normal}
.t-docparam{color:var(--t-docparam);font-style:normal}
#scopebar{
  position:fixed; left:0; right:0; bottom:0; z-index:40;
  display:flex; align-items:center; gap:.7rem;
  padding:.55rem clamp(1rem,4vw,2.5rem);
  background:var(--surface); border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:.78rem; color:var(--ink);
  box-shadow:0 -2px 12px rgba(0,0,0,.06);
}
#scopebar .tok{
  color:var(--ink-2); background:var(--rule-2); border-radius:3px; padding:.12rem .4rem;
  max-width:32ch; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:none;
}
#scopebar .sc{color:var(--accent); font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
#scopebar .idle{color:var(--muted); font-weight:400}
@media (max-width:600px){ #scopebar .tok{max-width:14ch} }
footer{margin-top:3rem; padding-top:1.3rem; border-top:1px solid var(--rule);
  font-size:.85rem; color:var(--muted); max-width:72ch}
footer code{font-family:"IBM Plex Mono",monospace; font-size:.9em}
"""

JS = """
(function () {
  var bar = document.getElementById('scopebar');
  var tok = bar.querySelector('.tok');
  var sc  = bar.querySelector('.sc');
  var hot = null;

  function idle() {
    if (hot) { hot.classList.remove('is-hot'); hot = null; }
    tok.hidden = true;
    sc.textContent = 'Hover any token to see how the grammar classified it';
    sc.classList.add('idle');
  }

  function show(el) {
    if (el === hot) return;
    if (hot) hot.classList.remove('is-hot');
    hot = el;
    el.classList.add('is-hot');
    var text = el.textContent.replace(/\\t/g, '\\u2192').replace(/\\n/g, ' ');
    tok.hidden = false;
    tok.textContent = text.length > 40 ? text.slice(0, 39) + '\\u2026' : text;
    sc.textContent = el.getAttribute('data-scope');
    sc.classList.remove('idle');
  }

  function handle(e) {
    var t = e.target;
    var el = t && t.nodeType === 1 ? t.closest('[data-scope]') : null;
    if (el) { show(el); } else if (hot) { idle(); }
  }

  document.addEventListener('mouseover', handle, { passive: true });
  document.addEventListener('focusin', handle, { passive: true });
  document.addEventListener('touchstart', handle, { passive: true });
  window.addEventListener('blur', idle);
  idle();
})();
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grammar", default=DEFAULT_GRAMMAR)
    ap.add_argument("--samples", default=None,
                    help="directory of .magik files to render in full beneath the "
                         "scope map; nothing is rendered there if this is omitted")
    ap.add_argument("--out", default=os.path.join(HERE, "preview.html"))
    args = ap.parse_args()

    grammar = Grammar(args.grammar)
    # The samples section is optional. Nothing is bundled for it -- point --samples
    # at Linguist's samples/Magik when this grammar is vendored there, or at any
    # checkout worth looking at.
    samples = args.samples or DEFAULT_SAMPLES
    explicit = args.samples is not None
    if os.path.isdir(samples):
        files = [(os.path.splitext(f)[0], os.path.join(samples, f))
                 for f in sorted(os.listdir(samples)) if f.endswith(".magik")]
    else:
        files = []
    if explicit and not files:
        sys.exit(f"no .magik samples found in {samples}")

    legend = "".join(f'<li><span class="sw t-{c}">&#9632;</span><code>{n}</code></li>'
                     for c, n in TOKENS)
    nav = "".join(f'<a href="#f-{k}">{os.path.basename(p)}</a>' for k, p in files)
    panes = "".join(f'<div id="f-{k}">{filepane(p, grammar)}</div>' for k, p in files)
    total = sum(len(open(p, encoding="utf8").read().rstrip("\n").split("\n")) for _, p in files)
    samples_section = ("""<section>
  <h2>The samples in full</h2>
  <p class="why">Real Magik, tokenized by the same grammar &mdash; code nobody wrote with this
  grammar in mind, which is where the surprises come from.</p>
  <div class="files-nav">%s</div>
  %s
</section>
""" % (nav, panes)) if files else ""
    sample_tag = (f'<span class="tag">{len(files)} samples &middot; {total} lines</span>'
                  if files else "")
    tour = block(open(os.path.join(HERE, "tour.magik"), encoding="utf8").read(), grammar)

    html_out = f"""<title>Magik Syntax Highlighting</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap">
<style>{CSS}</style>

<div class="wrap">
<header>
  <p class="eyebrow"><span class="chip"></span>magik.tmLanguage</p>
  <h1>What the Magik grammar scopes</h1>
  <p class="lede">Every line below is real tokenizer output &mdash; the grammar&rsquo;s own patterns
  run with TextMate&rsquo;s matching rules: leftmost match wins, ties go to whichever rule is listed
  first, <code>begin</code>/<code>end</code> rules held on a stack.</p>
  <div class="meta">
    <span class="tag">source.magik</span>
    {sample_tag}
  </div>
</header>

<section>
  <h2>The scope map</h2>
  <p class="why">One pass over the constructs the grammar distinguishes: exemplar and slot
  definitions, method and procedure calls, labels versus global references, piped identifiers,
  character literals, and all three documentation conventions &mdash; magik-tools TypeDoc,
  Smallworld UPPERCASE prose, and the sectioned method header.</p>
  <p class="hint"><kbd>hover</kbd> any token &mdash; its scope appears in the bar at the bottom.</p>
  {tour}
  <ul class="legend">{legend}</ul>
</section>

{samples_section}
<section>
  <h2>Known limits</h2>
  <p class="why">Short, and shorter than it was: three entries that used to sit here described
  compromises the grammar no longer makes, and one described a distinction Magik does not have.
  What is left is recorded in <span class="inline">TODO.md</span> so it is not re-reported as a bug.</p>
  <ul class="open">
    <li><b>One type claim survives, as a default rather than a guarantee.</b> In
    <code>_method trace_result.add(&hellip;)</code> the exemplar name scopes as
    <span class="inline">entity.name.type.class</span> &mdash; the only place the grammar still
    names a type. The position does not actually guarantee one:
    <span class="inline">EXEMPLAR_NAME</span> is an <span class="inline">IDENTIFIER</span>, so
    <code>a &lt;&lt; 10</code> followed by <code>_method a.example</code> defines the method on
    <code>integer</code>, the exemplar of whatever the name evaluates to. It is kept because methods
    are overwhelmingly defined on an exemplar named directly, so unlike the <code>def_*</code>
    claims this one is wrong only in proportion, not in kind.</li>
    <li><b><code>@generic</code> is scoped like <code>@param</code>, following the parser rather
    than the grammar.</b> The element both declares a generic and binds one, so it appears with and
    without a type. <span class="inline">TypeDocParser</span> reads a type node from it and
    <span class="inline">TypeDocMixedGenericsCheck</span> inspects those nodes &mdash; but
    <span class="inline">TypeDocGrammar</span> gives <code>GENERIC</code> no
    <code>optional(TYPE)</code>, unlike <code>PARAM</code>, <code>SLOT</code> and <code>LOOP</code>,
    so the braces fall through to the description and no type node is ever produced. Both forms are
    scoped here, which is what the parser expects and what people write.</li>
  </ul>
</section>

<footer>
  Generated by <code>tools/preview/build.py</code> in the grammar repository, which runs the
  grammar&rsquo;s patterns over the sample files with TextMate&rsquo;s resolution rules
  reimplemented directly. It is a faithful subset, not <code>vscode-textmate</code> itself, so treat
  it as a close preview rather than a byte-for-byte guarantee. Colours are an illustrative theme;
  GitHub applies its own.
</footer>
</div>

<div id="scopebar"><span class="tok" hidden></span><span class="sc"></span></div>
<script>{JS}</script>
"""
    with open(args.out, "w", encoding="utf8") as fh:
        fh.write(html_out)
    scoped = html_out.count("data-scope=")
    print(f"wrote {args.out} ({len(html_out):,} bytes, {scoped:,} scoped tokens)")


if __name__ == "__main__":
    main()
