# Building to a reference screenshot

When the user supplies an image and says "make it look like this", the image is
the specification. A technically-correct artifact that ignores the visual
language of the reference is a failed build, not a stylistic difference.

## 1. Extract the reference's vocabulary, not its pixels

Read the screenshot and list the concrete visual decisions before writing code:

| Axis | What to extract |
|---|---|
| Metaphor | A control panel of services, or a **room with people in it**? These are different products. |
| Layout skeleton | Sidebar + main canvas? Header + tabs + cards? |
| Status encoding | Coloured dots, text tags, both? Which words (`WORKING` / `IDLE` / `ONLINE`)? |
| Type | Monospace for names/status, sans for prose? |
| Palette | Background, surface, border, status green/grey/red as hex values. |

State the extracted vocabulary back to the user in one or two lines before
building. "This is an office with people at desks, not a status table" catches a
wrong-metaphor build before it costs an hour.

## 2. Metaphor mismatch is the #1 failure

The most expensive error is building the right *data* with the wrong *form*. A
table of service statuses, a card grid of the same services, and an isometric
office of the same services all satisfy "show me the agents and projects" — and
only one matches a screenshot of an office. When a reference image exists, the
metaphor is decided by the image.

If unsure, ask one question with the options rather than guessing; it is
cheaper than a rebuild.

## 3. Keep the real data plumbing from the previous attempt

Re-skinning an existing live panel is cheaper and safer than a new app: the
status endpoint, the auth gate, the nginx route and the systemd service are
already verified. Replace only the rendering layer (`control.html`) and keep
`_control_api` untouched unless the new view needs a new field.

## 4. Isometric SVG beats CSS 3D for a small office scene

CSS `transform-style: preserve-3d` with many absolutely-positioned children
yields non-deterministic geometry — rooms drift, walls face the wrong way,
hover transforms fight the scene transform, and you cannot debug it from the
markup. Compute the projection yourself:

```js
// classic 2:1 iso: (gx,gy) grid tile -> screen px
const TW = 64, TH = 32, WALLH = 34;
const iso = (gx, gy) => ({ x: (gx - gy) * TW / 2, y: (gx + gy) * TH / 2 });
// floor diamond of a w×h room centred at (cx,cy):
// M cx (cy-d) L (cx+w) cy L cx (cy+d) L (cx-w) cy Z
// back wall: (cx-w) cy -> (cx,cy+d) -> (cx,cy+d-WALLH) -> (cx-w) cy-WALLH
// side wall: (cx,cy+d) -> (cx+w) cy -> (cx+w) cy-WALLH -> (cx) cy+d-WALLH
```

Every shape is a polygon with coordinates you computed, so nothing overlaps by
accident. Render the whole scene as one `innerHTML` string of `<g>` groups.

## 5. Put per-item labels in a fixed legend strip, not under each shape

Labels placed under each room (`cy + d + 20`) land inside the neighbouring
row's floor and collide. A bottom strip of legend cards at hardcoded positions
cannot overlap anything and stays readable at any zoom:

```js
const LEG = [[40,560],[210,560],[380,560],[550,560],[720,560],[40,620],[210,620]];
```

Size the `viewBox` so the room grid and the legend strip never intersect, and
set the SVG CSS `height` to match the viewBox so nothing is cropped.

## 6. Verify in the browser, then LOOK at it

Curl proves the endpoint; only a headless browser proves the page renders. But
a rendered screenshot is not proof of *quality* — always inspect the pixels
yourself:

```python
pg.fill("#pw", PASSWORD); pg.click("#go"); pg.wait_for_timeout(2000)
pg.screenshot(path=out, full_page=True)
print("rooms:", pg.evaluate("document.querySelectorAll('#scene g.roomg').length"))
```

Then ask a vision check a **critical** question — "are there overlaps, is the
layout clean, are labels readable?" — not "does this look right?". Iterate on
the reported defects (spread the grid, move labels to the strip, adjust label
size) and re-screenshot. Two or three render-inspect-adjust rounds is normal
for a first version of any visual scene; budget for it instead of declaring
done after one render.

## 7. Resolve the user's own naming of things

Users name projects by their own shorthand, and those names often do not appear
in any file or KB note. When the user names an item, ask which real project it
is (or grep harder) rather than inventing a placeholder — then either rename
the KB file to the user's word or record the mapping in the note so the next
session resolves it without a search.
