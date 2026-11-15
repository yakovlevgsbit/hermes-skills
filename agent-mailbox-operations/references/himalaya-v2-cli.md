# himalaya v2 CLI cookbook

v2 (2.x) renamed most of the surface v1 gaidy describe; the config parser also
changed. Everything below was run against a live Gmail account.

## Config shape

Usage: `~/.config/himalaya/config.toml` (or `-c path`), one `[accounts.<name>]` block:

- `imap.server = "imaps://imap.gmail.com:993"` — bare authority means implicit TLS.
- `imap.sasl.plain.username` + `.password.command = ["cat", "/path/secret"]`.
- `smtp.server = "smtps://smtp.gmail.com:465"`, same auth block.
- `mailbox.alias.<role> = "<real folder>"` — NOT `[accounts.x.folder.alias]` (v1 form,
  silently ignored).

Template: `templates/himalaya-gmail.toml`.

## Reading

```bash
himalaya mailbox list                              # learn real folder names first
himalaya envelope list --page-size 10              # newest first
himalaya envelope search --page-size 5 "not flag seen"
himalaya envelope search --page-size 5 "from kwork"
himalaya envelope search --page-size 5 "after 2026-11-01 and from vk"
himalaya message read 141696                       # headers + MIME parts
himalaya message read 141696 --raw                 # original RFC 5322
himalaya message read 141696 --json                # parsed message
himalaya -m sent envelope list --page-size 3
himalaya attachment download 141696 --downloads-dir ~/dl
himalaya flag add 141696 --flag seen
himalaya message move "trash" 141696
```

Query language: `date <yyyy-mm-dd>`, `after <yyyy-mm-dd>`, `from <p>`, `to <p>`,
`subject <p>`, `body <p>`, `flag <seen|answered|flagged|draft>`, joined by
`and` / `or` / `not`, parentheses, `order by date desc`.

Two syntax traps:

1. Conditions are **space-separated** (`from kwork`); `from:kwork` is a parse error.
2. Options must come **before** the query: `envelope search --page-size 5 "not flag seen"`.
   After the query they are consumed as query text and the parser fails on `-`.

## Sending (only if SMTP is reachable)

```bash
printf 'From: Name <a@b.ru>\nTo: c@d.ru\nSubject: Hi\n\nBody\n' | himalaya message send
```

`message send` reads MIME (or an MML body) from stdin — there is no `template send`
anymore. `--save <mailbox>` controls the Sent copy; on Gmail leave it unset.
`message compose`, `message reply <id>`, `message forward <id>` take flags and open
`$EDITOR` when not given a body — pipe instead.

## Verification sequence

1. `mailbox list` → folders render.
2. `envelope list --page-size 5` → subjects and senders appear.
3. `message read <id>` → headers and body decode.
4. Send to your own address, then `-m sent envelope list --page-size 3` → the message
   is there with your From.

## When SMTP is blocked

`smtp.gmail.com:465/587` refusing while 993/443 work means the host filters SMTP:
reading stays on IMAP here, sending moves to the provider API —
`references/gmail-api-send.md`.
