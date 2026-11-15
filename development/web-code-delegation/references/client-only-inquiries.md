# Client-only inquiry forms

Use when a static landing page has no submission backend and must help a visitor
prepare a real message to an audited contact, without pretending to send it.

## Implementation sequence

1. **Keep a direct contact link as the baseline.** Hide or disable the draft form
   until its handlers are attached; show the direct link without JavaScript. Do
   not allow a failed enhancement to serialize contact details into a GET query
   or POST to a nonexistent endpoint. On a page with no server-bound forms,
   `form-action 'none'` provides an additional CSP guard.
2. **Validate before preparing.** Associate visible labels and inline errors with
   each field, set `aria-invalid`, and focus the first invalid field. Check trimmed
   required values and bounds in code as well as HTML constraints, including
   optional fields: `form.noValidate` and programmatic values can bypass
   `maxlength` even when ordinary typing is capped. Give each bounded optional
   field an associated error node; open a closed ancestor `details` before
   focusing its invalid field. Test empty optional input, exact maximum, maximum
   plus one and recovery. Accept the contact formats the UI advertises.
3. **Commit the active field before taking the draft snapshot.** Finish its native
   change/blur event before recording the input revision; otherwise moving focus
   to the result can invalidate the draft that was just created. Read the selected
   service from the real option, not a separately maintained label map.
4. **Build plain text, not HTML.** Write the draft through `textarea.value` or
   `textContent`; preserve Unicode, punctuation and literal angle brackets. Do not
   store entered details in cookies/localStorage, telemetry or the current page's
   URL. Expose an actual preparation busy state and restore controls in `finally`.
5. **Construct a destination-specific draft link.** Telegram public-username links
   support `https://t.me/<audited_username>?text=<encoded_text>`; check the official
   specification at https://core.telegram.org/api/links#public-username-links when
   changing this transport. Build the link without navigating on form submission.
   Say that the message is not sent and must be confirmed inside the messenger.
6. **Fall back without truncation.** Choose and test a conservative maximum URL
   length as an application policy, not a claimed protocol limit. If the encoded
   link exceeds it, or `encodeURIComponent` rejects an unpaired surrogate, retain
   the full draft and offer copy-then-open with a plain recipient link. Update the
   accessible link name and instructions so they no longer promise prefilled text.
7. **Report clipboard results truthfully.** Await `navigator.clipboard.writeText`
   before announcing success. If permission is denied or the API is absent, focus
   and select the readonly draft and give desktop/phone copying instructions.
   Catch the failure and release the busy state; do not replace it with a false
   success message.
8. **Invalidate stale output on every edit.** Include text input, select changes
   and service-card prefills. Hide/clear the old draft, reset its link and clear
   copy feedback. Increment a revision counter; after each awaited preparation or
   clipboard operation, ignore UI updates from an older revision. Ignoring a late
   clipboard result prevents stale success feedback; it does not undo an OS copy.

## Browser test matrix

| Path | Required observation |
|---|---|
| Empty, whitespace, malformed contact, overlength values | Inline error, correct focus, no draft or navigation |
| Every service CTA | Exact option selected; contact anchor and input focus work |
| Valid trimmed input | Full readable draft and exact recipient link |
| Unicode and HTML-like text | Literal text preserved; no DOM insertion or exception |
| URL-length boundary | Prefill within policy; full-text copying beyond it |
| Edit after prepare or during an awaited operation | No usable stale draft or stale success message |
| Clipboard success, denial and missing API | Real clipboard contents or selectable-text recovery |
| JavaScript disabled | Direct contact remains usable; fields do not submit |
| Prepare only | No message sent, popup, PII-bearing navigation or storage write |

Observe requests after the action rather than inferring submission from button
text. Distinguish harmless lazy-loaded image/font GETs caused by scrolling from
form-data requests; assert no PII transmission or unintended write/navigation.
Test preparation without actually sending a message to the owner's account.
