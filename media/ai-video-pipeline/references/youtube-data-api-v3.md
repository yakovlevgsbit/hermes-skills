# YouTube Data API v3 — upload

## Two token paths

- **OAuth user token** — required for uploads. A service account cannot upload to a
  user's channel in the usual flow; if uploads fail with permission errors, source the
  token from the user's own OAuth grant (a refresh token stored alongside the account).
- **Service account** — useful for quota/project management only. It has no upload rights
  on a user channel.

## Token handling

- Access tokens expire in about an hour. Refresh before use, and keep the refresh token —
  it is the durable credential.
- Persist the new access token with its expiry, and always allow a safety margin so a
  long upload does not expire mid-flight.
- A scheduled job must not trust a cached token: refresh it on every run. A stale cached
  token only surfaces as an error at request time.

## Resumable upload

1. `POST` to the upload endpoint with `uploadType=resumable&part=snippet,status` and
   headers `X-Upload-Content-Type` / `X-Upload-Content-Length`. The response `Location`
   header is the resumable session URL.
2. `PUT` chunks with `Content-Range: bytes <start>-<end>/<total>`.
3. `308` means continue; advance the offset from the `Range` response header. `200/201`
   returns the video resource.

Upload in ~1MB chunks — large single requests time out on big files.

## Status and privacy

- `privacyStatus`: `public` | `unlisted` | `private`.
- Decide deliberately. A pipeline that publishes publicly is irreversible through the API
  if the token lacks delete scope — check the granted scopes before choosing.
- After upload, read the video back (`videos.list`) to confirm `uploadStatus` and
  `processingStatus`. A successful response body alone is not proof.

## Quota and limits

- **`search.list` is the expensive call: 100 units per request.** Against the default
  10,000-unit daily budget that is ~100 searches a day, TOTAL. Budget it like money:
  count the searches you intend to make (including variant queries per topic —
  `"supra"` and `"supra shorts"` are TWO searches) before running, and persist a
  per-day usage counter so a scheduled job cannot burn the budget unnoticed. `videos.list`,
  `channels.list` and `playlistItems.list` are 1 unit each, so batching those is free.
- **Daily upload cap per channel.** When exceeded, the API returns a limit error and NO
  further uploads succeed until the quota resets. This is per-channel, not per-token, and
  cannot be raised from the client.
- Handle it as a soft failure: keep the generated artefact, mark the queue row
  `quota_exceeded`, and retry later.
- The search/list endpoints only return `public` videos. A freshly uploaded `unlisted`
  video will NOT appear in a channel listing — verify it by direct video ID instead, or
  you will wrongly conclude the upload failed.

## Response shape differs per endpoint — do not share a parser

Reading the same field from two endpoints is the classic silent-empty-bug source.

| Endpoint | Video id lives at |
|---|---|
| `search.list` | `items[].id.videoId` |
| `videos.list` | `items[].id` |
| `playlistItems.list` | `items[].contentDetails.videoId` |

Copying the `snippet.resourceId.videoId` path (correct for a playlist) into a
`videos.list` reader returns an empty id on every row, and an empty id still renders
as a well-formed link (`https://youtu.be/`) — so the output looks right and is
unusable. Assert the id is non-empty before printing links.

## `channels.list` needs `part=contentDetails` for the uploads playlist

The `snippet,statistics` parts do NOT include `contentDetails.relatedPlaylists.uploads`,
which is the only way to enumerate a channel's own uploads. Requesting without it
returns a valid, populated channel object with no playlist field — the code then
falls through to a degraded path rather than erroring, so the missing part is
invisible until you inspect the response. Always request
`part=snippet,statistics,contentDetails` when you intend to walk a channel's history.

## Measuring what made a video take off

To judge whether a video outperformed its own channel, normalise by the channel's
history — not by the search results you happened to collect.

```
views_per_day = views / max(age_in_days, 1)
vs_channel    = views_per_day / median(views_per_day of the channel's uploads)
```

- **The median MUST come from the channel's uploads playlist**, not from the search
  result set. A search ordered by `viewCount` returns already-successful videos, so
  its median is the median of the winners and every candidate looks average — the
  outliers you were hunting are the baseline.
- **Compute `contentDetails.duration` for free while you are there** if format matters
  (e.g. distinguishing Shorts from long-form); `videos.list` accepts multiple `part`
  values in one call.

## A silent fallback hides a broken primary path

When a cheaper/degraded alternative exists for a primary path, the code will take it
without complaint and report a plausible result. A median computed from the search
result set after the uploads playlist was unavailable produced perfectly well-formed
numbers that were wrong in the permissive direction — ranking nothing as notable.

- **Log the path actually taken** (primary vs fallback) at the point of divergence, so
  the report says which basis the numbers rest on.
- **Fail loudly, or emit a distinct label**, when the primary source is unavailable — a
  fallback that returns the same shape as success is indistinguishable from it.
- **Verify the primary path on a known case** where you already know the expected answer
  before trusting the pipeline that produces it.

## Error interpretation

Always surface the provider's INNER message. A bare `HTTP 400` hides the actual cause
(limit exceeded, invalid field, unsupported value). Parse the JSON error body and log
`error.message` plus `errors[].reason`.

## Verification checklist

1. Video is readable by ID and reports `uploadStatus: uploaded`.
2. Title/description match the intended channel convention.
3. Duration matches the requested length.
4. `privacyStatus` is the intended value.
