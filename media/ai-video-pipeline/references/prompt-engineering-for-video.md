# Prompt engineering for AI video

## Structure that works

Write prompts in sections and keep them in this order:

1. **Main subject** — exact make/model, paint, wheels, body kit, distinguishing features.
2. **Environment** — location, time of day, weather, road surface, background detail.
3. **Action** — ONE clear primary action achievable inside the duration.
4. **Camera** — opening / middle / final shot, using concrete moves (low-angle tracking,
   dolly-in, orbit, overhead, slow push-in). No contradictory moves, no excessive cuts.
5. **Lighting and effects** — only what supports the scene; do not pile on every effect.
6. **Art direction** — the channel's signature look.
7. **Consistency constraints** — identical geometry, preserve paint/wheels, no morphing,
   no extra vehicles, no text overlays.

## Rotate three axes independently

A "batch" that varies only the car reads as the same video. Rotate all three:

- **Environment** — the biggest visual differentiator. Keep a list (20-30 entries) of
  distinct settings spanning time of day, weather and location type. Pick the next one
  that is not in the recent history.
- **Action** — what the car does (launch, drift, brake, cruise, burnout, drive-by).
- **Camera** — the shot vocabulary.

Store the chosen environment index in the queue row so the rotation can exclude recent
choices. Without persistence the rotation degrades to random repeats.

## Hard requirements to state explicitly

- Exact duration ("EXACTLY 10 SECONDS") — models default to 30-45s otherwise.
- Aspect ratio and orientation.
- "No text overlays, no watermarks" — models add them unless told not to.
- "Strong opening in the first 1-2 seconds" — for short-form, the hook is the product.

## Failure modes

- **Repetition of one background** — a hard-coded scene in the prompt. See pitfall 1 in
  SKILL.md.
- **Model parrots the topic into a metadata field** — split the topic before sending, and
  validate the returned field.
- **Generic object substitution** — the model returns "sports car" instead of the subject.
  Accept a value only if it names the subject; otherwise fall back to parsing the topic.
- **Truncated JSON** — raise `max_tokens`; check for the required keys before trusting it.
- **Duration drift** — always re-read the duration from the generated artefact.
