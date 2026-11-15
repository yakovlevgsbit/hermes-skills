# Series variation — recipes and detectors

Depth behind `generative-media-api-generation`. How to make N similar artifacts
look like a varied feed instead of N copies of one scene.

## The failure mode

A channel publishes a reel every few hours from a template that rotates the car
but hardcodes the setting:

```
"image_prompt": "... Night scene, neon, sakura petals, Japanese street, car centered."
```

Every output is a different car in the same wet neon alley. Nothing errors. The
first item looks great. The problem only becomes visible when you diff the
prompt fields across a batch.

Root cause is usually not a bug — it is a field that was written as a constant
and never noticed because the *subject* was the axis being varied.

## Detect a pinned axis before building anything

Compare the generated fields, not the titles:

```python
# N most recent rows; if one phrase dominates, that field is a constant
import re, collections
def env_of(prompt):
    m = re.search(r"in (.+?)(?:,|\.|$)", prompt)
    return m.group(1).strip() if m else "?"

rows = fetch_recent(n=8)                     # whatever your store is
print(collections.Counter(env_of(r["image_prompt"]) for r in rows))
```

A distribution where one environment covers 6 of 8 rows means the environment is
pinned. Titles will not show this — they are deliberately varied by design.

Check every prompt field you emit, including the ones that look like flavour.

## Rotation recipe

1. **List the axes** and write 20–30 concrete values for each. Concrete beats
   generic: `underground parking garage, fluorescent tubes and concrete pillars`
   not `a garage`.
2. **Derive the index from persisted state, not from a counter in code.** Store
   the chosen index on the artifact. On the next run, exclude the indices seen in
   the last N rows. This survives restarts and works across multiple writers.
3. **Seed the offset from the row count** so the rotation walks the list instead of
   restarting at element 0 every run:

   ```python
   offset = len(all_rows)
   for i in range(len(ENVIRONMENTS)):
       idx = (offset + i) % len(ENVIRONMENTS)
       if idx not in used:
           return idx
   ```

4. **Verify with a simulation, not by reasoning about it.** Run the picker N times
   feeding each result back as used, and assert the picks are distinct:

   ```python
   used = []
   picked = []
   for n in range(6):
       t = pick(used, seed=n)
       assert t not in picked, f"repeat: {t}"
       picked.append(t); used.insert(0, t)
   ```

5. **Pass the value as an instruction, and pass the used ones as a prohibition.**
   The model will otherwise fall back to the most stereotyped setting for the
   niche (neon rain street for cars) every single time.

## Title vs description is a policy, so derive both defensively

A channel's title/description convention is a standing rule, not something to
re-derive per run. Typical shape:

| Field | Content |
|---|---|
| title | the subject ONLY — no action, no place, no hashtags |
| description | tags ONLY, space-separated, no prose |

The model does not know this convention. Two failure modes, both silent:

- **It copies the topic into the title.** If the topic is
  `"Toyota AE86 Trueno idling, engine rumbling, then revving once"`, the title
  becomes that whole string. Pass only the subject as the topic, AND strip
  action words from the title field defensively — do not rely on the prompt
  alone, because the topic you hand the model leaks.
- **It merges tags.** `#GT-R` + `#R34` → `#GTRR34` is a different, useless tag.
  Split on explicit merge patterns and de-duplicate case-insensitively.

Keep the source of truth for the title as a short normaliser that returns the
subject even when the model misbehaves:

```python
ACTION_WORDS = re.compile(r"\b(idling|revving|rumbling|launching|drifting|drift|"
                          r"accelerating|cruising|braking|traction|engine)\b", re.I)

for cut in (" launching", " drifting", " accelerating", " idling",
            " parked", " in ", " at ", " on ", " with ", " under "):
    t = t.split(cut)[0]
```

Verify the title after the run by asserting it contains none of the action
words — the assertion is cheap and catches the regression immediately.

## Schema drift after a prompt rewrite

Rewriting a template for quality can quietly drop a field the pipeline needs.
The run still exits 0; the missing value surfaces later as an empty column or a
broken upload.

After editing a prompt template, **re-run the parse and assert every required
field is present and non-empty** — do not check only that JSON parsed:

```python
required = ("key_object", "video_prompt", "image_prompt", "hashtags")
missing = [f for f in required if not pkg.get(f)]
if missing:
    raise RuntimeError(f"prompt template dropped fields: {missing}")
```

A richer template is the most likely time to lose a field, so treat the rewrite as
a schema change and test it as one.

## Cron wrapper contract

A wrapper exists because the scheduler rejects symlinks outside its scripts dir,
so it re-executes the real script:

```python
import subprocess, sys
rc = subprocess.call([sys.executable, "/path/to/real_pipeline.py"] + sys.argv[1:])
sys.exit(rc)
```

Two ways this goes wrong, both expensive:

- **Not forwarding `sys.argv`** — `--dry-run` is ignored, the wrapper runs the
  full pipeline, and the "free" test spends real money. Always forward argv.
- **Not propagating the child's exit code** — a run that crashes 30 seconds in
  reports `ok` to the scheduler and the delivery is empty. In no-agent mode the
  script's stdout *is* the notification, so a silent success looks identical to a
  working run. Always `sys.exit(rc)`.

Confirm both before trusting the schedule: run the wrapper by hand with
`--dry-run` and check it stops early, then check the exit code is non-zero when
you force a failure.

## Scheduler status is not job status

`cron list` showing `ok` means the scheduler handed the job off — it does not
mean the script did anything. Read the per-job output file (under the scheduler's
`cron/output/<job_id>/` directory) to see what the script actually printed, and
query the artifact store for the row the run should have created. A `completed`
execution with no new row is a crashed run that was reported as healthy.
