# Telegram bot: risks that change the quote

## File size limits (Bot API)

- Download via `getFile`: 20 MB ceiling. Larger source files (CDR, DXF, big PDF)
  cannot be fetched by the bot.
- Send from the bot: 50 MB ceiling.
- Fix without extra infrastructure: `forward_message` to the manager — the
  original keeps full quality and any size.
- To *store* large originals: self-hosted local Bot API server (up to ~2 GB),
  extra service to run — quote it as its own line.

## JSON output from the model

A cheap model often ignores a "reply in JSON" instruction written only in the
prompt. Use the API's structured-output mode (`response_format={"type":
"json_object"}`) and keep a strict retry. Without it the model answers in prose
and the parsed fields come back empty.

## Field collection

Merge model-returned fields with what is already stored, only writing non-empty
values — otherwise the model blanks out facts it already gathered earlier in
the dialog.

## Cost

Cheap model per dialog ≈ 0,3–0,5 ₽; give the client a monthly number at their
volume.
