# Cleaning LaTeX out of a data column

Applies when a knowledge-base column was converted from PDF and carries
`$...$`, `\text{...}`, `\cdot`, `\pm`, `\Omega`, `{,}` and friends. The model
forwards these verbatim to chat, so the column is cleaned as data — asking the
model to be careful does not work.

## Trap 1: `{,}` is an EMPTY group holding a comma, not `{,5}`

The single most misread construct, and guessing it wrong fails silently and
partially:

```
84{,}0     characters:  8 4 { , } 0
                        └─ the digit is AFTER the closing brace ─┘
```

A rule written as `\{,(\d)\}` (digit inside the braces) matches **nothing** in
this data. So does `\{,(\d{2})\}` — there is nothing between `{` and `}` at all.
The only correct rule is a literal:

```python
s = s.replace(r'{,}', ',')     # 84{,}0 -> 84,0 ; 13{,}75 -> 13,75
```

Dump the offending string character-by-character before writing any rule.
One `print(list(enumerate(sample)))` settles it in a second; guessing costs a
full re-run and, worse, a plausible-looking partial result.

## Trap 2: substitution order

`\circ` sits inside `^{\circ}`, `\text{C}` inside a math span, `^3` after
`\text{}`. Substitute in this order or you ship `180^{°}` with stray braces:

1. `{,}` -> `,`
2. named commands -> Unicode (`\cdot`→`·`, `\times`→`×`, `\pm`→`±`,
   `\Omega`→`Ом`, `\varnothing`→`Ø`, `\%`→`%`)
3. degrees: strip `^{\circ}` and `^\circ` -> `°`
4. `\text{...}` -> contents, repeat until stable (handles nesting)
5. spacing macros `\,` `\;` `\:` `\!` and `\ ` -> space
6. numeric powers `^3`/`^{3}` -> `³`/`²` (single digits only)
7. `$...$` -> contents, then any stray `$`
8. subscripts `_b` -> `b`
9. collapse spaces, then re-join digit-group separators: `10\,990` -> `10990`

## Gate the conversion on a residue check, apply nothing if it fails

The cheap guard that catches both traps: after converting, test for surviving
LaTeX and **do not write a row that still has any**:

```python
RESIDUE = re.compile(r'\\[a-zA-Z]+|\$|\{|\}')
bad = RESIDUE.search(new)
if bad:                      # keep the ORIGINAL, record for review
    flagged.append((rid, bad.group(0), old, new))
    out[rid] = old
```

This guard is why a "clean" run can still be wrong. When rows come back flagged,
read the residue token they report — it names the construct you got wrong
(`{` points at the `{,}` rule, not at a stray brace elsewhere).

## Numbers are the invariant; diff them and expect false positives

Assert the multiset of numbers is unchanged, then **triage every reported diff
by hand**. These classes are guaranteed artifacts of a checker that read the
un-normalized source:

| diff reported | actually |
|---|---|
| `162` -> `16`,`2` | `16\pm2` -> `16±2`: `\pm` not stripped when the checker read it |
| `089` -> `89`,`0` | `89{,}0` -> `89,0`: same `{,}` trap, in the checker |
| `1200200` -> `1200`,`200` | `1200\pm200`, same |
| `10`,`990` -> `10990` | `10\,990`: checker read the spacing macro as a separator |

Report them as "checker artifacts, verified individually", never as "N records
changed". A diff you have not explained is not a pass.

## Hand-written replacement answers go through the converter too

When editing rows by hand (dropping one model's figures, merging two questions
into one), the hand-typed `answer` arrives full of `$` and `\text{}` again.
Route it through the same function before assembling the payload, and re-run
the residue assertion on the **final** rows. A pre-payload check caught exactly
this, four rows, before anything was written.