---
name: browser-admin-console
description: "Use when a setting exists only in a vendor's web console."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [browser, admin-panel, react, credentials, scopes, verification]
    related_skills: [service-credentials-vault, tilda-mcp-official]
---

# Driving a vendor admin console

## When to use

A setting lives only in a logged-in web console — API key scopes, plan or tenant
settings, bot registration, webhook URLs — and there is no API for it, or the API
route is already broken. Also when a key exists but its permissions must change.

The deliverable is a verified change: the control moved **and** the new permission
works through the interface that will actually use it. A saved form is not proof.

## Procedure

1. Log in through the credential vault: type the identifier, let the vault fill the
   password, submit. Never type, echo or ask for a password or a one-time code.
2. Find the control in the DOM and read the surrounding markup first — the modal's
   `outerHTML` tells you whether the fields are native `input`/`select` or a React
   state machine, and that decides the click strategy below.
3. Act, then **re-read the state** in the same call. A click that reports success
   and a state that reverted are both "success" at the API level.
4. Reload the page and confirm the value persisted server-side. Optimistic UI shows
   unsaved changes as saved.
5. Prove the effect through the consumer: call the API or agent that needs the
   permission and check it now succeeds (and that it still fails where it should).
   Check both directions — the granted target works AND every neighbouring
   entity is still refused; a credential that works everywhere is a mistake, not
   a success.
6. Record the outcome in the KB — which entity was changed, what was granted, masked
   identifiers of the other credentials and their expiries. Never the secret value.

## Pitfalls

- **React reverts synthetic clicks.** `element.click()` from JS on a checkbox or an
  option reports `checked: true` and the component re-renders it back. Click the
  `<label for="...">` at its rectangle, or set the native value with the prototype
  setter and dispatch a real `change` event. Verify with a fresh read of the ids.
- **A dropdown item below the fold is not clicked.** Default viewport height is
  around 577 px, so a menu that opens near the bottom of a table misses silently and
  no dialog appears. Raise the viewport (`Emulation.setDeviceMetricsOverride` with
  height 1000), then take coordinates from `getBoundingClientRect` in the same call
  as the click.
- **Confirm dialogs sit outside the component tree.** Read the dialog text and
  assert it names the entity you intend before confirming; the confirm control is
  often a bare `<input type="button" class="…popup-yes">`, not a visible button.
- **One-time secrets are in a field, not in the text.** A key shown once lives in an
  `input`/`code` element's `.value`; `innerText` does not contain it, and the modal
  closes on its own. Extract and write it to the secrets file in the same call, and
  print only a prefix/suffix mask.
- **A control that "is not there" is often behind a collapsed custom select, not missing.** A scope toggle can render as `<select name="projects_access">` whose options are `Все проекты` / `Выбранные`; matching on visible text finds nothing because the options live inside an unopened `<select>`. Enumerate `select` names and `option` values first, set `sel.value` + dispatch `change`, then re-read which checkboxes became `offsetParent`-visible — the dependent list usually renders only after the mode switch.
- **Order the mode switch before the dependent selections.** Choosing checkboxes first and switching the mode afterwards leaves the earlier selection attached to the other mode, so a credential comes out with account-wide scope when you meant one item (or empty when you meant all). Verify the final state by reading every checkbox's `checked`, not by trusting the clicks.
- **Creating an account-level object may require account-wide scope you must not keep.** When the console says creation needs full-account rights, create the object through the browser form instead of widening the working credential, then mint a fresh credential scoped to just the new object. Treat any full-account credential you created meanwhile as an incident: delete it in the same session and confirm the count dropped.
- **A persisted UI value is not a granted permission.** When the console shows the
  new scope after a reload and the consumer still answers "forbidden", the edit did
  not propagate: issue a new credential with the scope instead of re-editing the old
  one, then prove it with the consumer.
- **Editing one credential can silently be the wrong one.** Console tables show
  masked keys; match the mask against the stored secret's prefix and suffix before
  touching a row, and check the "last used" column to see which key is actually live.
- **Sessions drop between navigations.** Re-authenticate through the vault rather
  than reusing stale cookies; a login redirect mid-flow looks like a missing page.

## Reporting

State the entity changed, the resulting scope in words, the evidence from the
consumer call, and which other credentials remain (with expiry dates) so the user
can decide about cleanup. Offer deletions; do not perform them unasked.
