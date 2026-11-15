# Getting bytes in and out of cloud storage

A media job usually needs a source file *from* somewhere and a finished artifact
*back to* somewhere. When either leg is cloud storage, the failure is almost never
in the media call — it is in whether the credential can read, or the provider can
fetch. Diagnose the leg before touching the generation code.

## Probe both directions before designing anything

A storage credential is scoped per **operation**, and the scopes are granted
independently. A token that writes perfectly may not be able to list or download
anything. Probe every direction you actually need, not just the one that looks
broken:

| Direction | Probe | Typical success code |
|---|---|---|
| create folder / path | `PUT /resources?path=...` | 201 |
| upload | `GET /resources/upload` then `PUT` the returned href | 201 |
| publish / share | `PUT /resources/publish` | 200 |
| **list** | `GET /resources?path=<root>` | 200 |
| **read by exact path** | `GET /resources?path=<known path>` | 200 |
| **download** | `GET /resources/download` | 200 + href |
| delete | `DELETE /resources` | 204 |

Do all of these in one pass and record the code for each. A table with four 201s
and three 403s tells you the scope is write-only, which is a different problem from
a wrong token and a different problem again from a missing API enablement.

## Three failures that all look like "access denied"

Read the error body before naming the cause — these are distinguishable:

1. **API not enabled at all** — the provider has never seen the API on the project.
   The message names the API and a project and links a console enablement page.
   Fixing this needs a human in the cloud console; no code change reaches it.
2. **Enabled but no scope / no share** — the API exists and the credential is
   accepted, but the operation is out of scope or the target object is not shared
   with this identity. `403` with a permission message and no project link.
3. **Wrong identity for the object** — a service account can mint a valid token and
   still see nothing, because the file belongs to a different account's drive.
   A folder shared with the service account's own email is the usual fix; sharing
   a folder does **not** grant a service account access to files it cannot see
   through its own identity.

For a media pipeline, case 2 and 3 are the ones that bite: the token is fine, the
API is enabled, and reading still returns nothing.

## The provider also needs to REACH the bytes

Even with a fully working storage read, the media provider may not be able to
fetch the source frame. Two independent reachability problems, both of which
produce a job that accepts and then fails at poll time:

- **The provider fetches by public URL.** A private storage link — a signed URL, a
  share link that needs a session, or a path only your credential can read — is
  unreachable to it. The job is created, then fails with a download error.
- **The cert chain must be publicly valid.** A self-signed certificate is rejected
  even when the same URL fetches fine with `curl -k` locally.

So the reachability chain is: *storage credential → public https URL → provider's
fetch*. Break any link and the generation fails, and the error names the provider
side, not yours.

## When the read leg is blocked, invert the pipeline

Do not stall the whole job on an unreadable input. Split it at a boundary you
control:

- **Input from a local folder or a chat attachment**, output to the writable store.
  This works the moment the write scope is confirmed, with no console changes.
- Keep the generation step identical; only the file transport changes. A pipeline
  that reads from a folder and writes to storage is the same code as one that
  reads storage and writes storage, with the transport swapped.

State plainly which leg is blocked and what it would take to unblock it (enable an
API, grant a scope, share a folder). Do not present the inverted pipeline as the
same as the requested one.

## Automated sign-in to a cloud console is a dead end

A headless browser is usually refused at the account sign-in step with a message
about the browser not being secure — this is the provider blocking automation, not
a missing password. A saved credential does not help, because the block is on the
automation itself.

Enabling an API or granting an IAM permission is likewise not reachable through
the storage API: the same credential that reads files returns a permission error
when asked to list or enable services. These are human-in-console actions.

Report the exact console step and move on with the working alternative. Do not
spend the session retrying the login.

## Verify a storage write by reading back through a different route

An upload returning 201 proves the bytes were accepted, not that they are visible
where you think. Publish/share the object, then confirm the public URL returns the
same byte count as the local file. A share link that resolves to a login page
returns HTTP 200 with the wrong body, exactly like the media-frame failure above.
