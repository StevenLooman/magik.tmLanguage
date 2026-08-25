# magik.tmLanguage

A TextMate grammar for [Magik](https://en.wikipedia.org/wiki/Magik_(programming_language)),
the language of the Smallworld platform.

Scope name: `source.magik`

## Using it

**VS Code**: point a `grammars` contribution at `grammars/magik.tmLanguage.json`:

```json
"contributes": {
  "grammars": [
    {
      "language": "magik",
      "scopeName": "source.magik",
      "path": "./grammars/magik.tmLanguage.json"
    }
  ]
}
```

**Linguist**: vendored as a submodule and mapped from `languages.yml`:

```yaml
Magik:
  type: programming
  color: "#005cb9"
  extensions:
  - ".magik"
  tm_scope: source.magik
  ace_mode: text
```

Anything else that reads TextMate grammars (Sublime Text, TextMate, Zed, ...) can
consume the same file.

## What it scopes

Sixteen rules, forty patterns, thirty-six distinct scopes.

| construct | scope |
|---|---|
| keywords | `keyword.control.{conditional,loop,exception,flow}`, `keyword.other` |
| modifiers and declarations | `storage.type`, `storage.modifier`, `storage.modifier.parameter` |
| method definitions | `storage.type.function`, `entity.name.type.class`, `entity.name.function.definition` |
| method and procedure calls | `entity.name.function` |
| slots | `variable.other.property` |
| `_self`, `_clone`, `_super`, `_thisthread` | `variable.language` |
| `!name!` | `variable.language.global` |
| `@name` | `variable.other.global` |
| labels after `_leave`, `_continue`, `_block`, `_loop`, `_endloop`, `_proc` | `entity.name.label` |
| symbols, including `:\|piped\|` | `constant.other.symbol` |
| character literals `%a`, `%space`, `%"` | `constant.character` |
| strings | `string.quoted.{double,single}` |
| `_true`, `_false`, `_maybe` | `constant.language.boolean` |
| `_unset` | `constant.language.unset` |
| `>>` | `keyword.other.emit` |
| operators | `keyword.operator.{assignment,comparison,arithmetic,logical}` |
| comments | `comment.line.number-sign`, `comment.block.documentation` |
| `FIXME`, `TODO`, `DEBUG` | `keyword.other.todo` |
| magik-tools TypeDoc | `keyword.other.documentation`, `entity.name.type.documentation`, `variable.parameter.documentation` |

Piped identifiers (`|name with spaces|`) and package prefixes (`sw:rope`) are
handled wherever an identifier can appear.

Three documentation conventions coexist in real Magik and all three are
supported: magik-tools TypeDoc (`@param`, `@return`, `@loop`, `@slot`,
`@generic`, `@invokes_method`), Smallworld prose with parameter names in
uppercase, and the sectioned `Parameters:` / `Returns:` / `Function:` header.
Only TypeDoc gets extra scopes — the other two are prose, and there is nothing
in them a theme could usefully colour.

## Layout

| path | |
|---|---|
| `grammars/magik.tmLanguage.json` | the grammar |
| `tools/preview/` | a preview page generator and a corpus auditor |

## Development

Two tools help, both dependency-free:

```sh
python3 tools/preview/build.py                 # render a preview page
python3 tools/preview/audit.py /path/to/magik  # audit a corpus
```

`build.py` renders a page from the sample files in this repository, with every
token carrying its scope name on hover. Those files were written to exercise the
grammar, so the page shows it handling constructs someone already thought of.

`audit.py` is the opposite: point it at a Magik source files and
it tokenizes the contents, reporting identifiers split across scopes, unscoped
keywords or literals, runaway strings, and unrecognised method definitions.

Worth knowing when editing:

- **Order decides ties.** The leftmost match wins, and at equal offsets the rule
  listed first in `patterns` wins.
- **`begin`/`end` replaces the pattern set.** While such a rule is open, only its
  own `patterns` apply.
- **Keep lookbehinds fixed-width.** PCRE and Oniguruma accept multi-length
  alternatives; Python's `re` does not, and the preview tools use it. Writing
  `(?:(?<=_leave)|(?<=_continue))` rather than `(?<=_leave|_continue)` keeps the
  grammar portable across all three.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
