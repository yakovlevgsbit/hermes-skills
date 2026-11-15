# VK publishing recipe

## Token split (VK is forced by API design in 2026)

- **Photo upload** must use a **USER token** (scope: `photos`). A community token returns `error 27`/`code 15` on `photos.getWallUploadServer`.
- **wall.post** must use a **COMMUNITY token** (owner_id = `-group_id`).
- The community token is the easy half (created in group admin panel → «Работа с API» → token). The user token is the scarce half and needs `photos` scope.

## wall.post payload

```
owner_id = -abs(group_id)
message       = text (max 16384 chars)
from_group    = 1
attachments   = "photo{owner}_{id}[{access_key}]"  (optional, up to 10)
```

## Photo upload 4 calls

1. `photos.getWallUploadServer` (user token, group_id) → `upload_url`
2. `POST` the file to `upload_url` (field name: `photo`) → `server/photo/hash`
3. `photos.saveWallPhoto` (user token) → `{id, owner_id, access_key}`
4. `wall.post` (community token) → `post_id`

## Verified things

- `users.get` with `fields=screen_name` validates a user token.
- `groups.getById` with `fields=members_count,screen_name` resolves a group reference (bare id, negative id, or screen name). VK normalises screen names (`public204149473` → `club204149473`).
- `photos.getWallUploadServer` is the honest probe for "does photo posting work" — a community token fails this before you build the whole post.
- `wall.post` must return `post_id`. `error_code 5` = token expired, `214` = token has no access to this group (needs admin rights), `6` = rate limit — wait a minute.
- Video posting (`video.save`) is CLOSED: VK ID no longer issues the `video` scope. Do not build a video path on VK.

## DB-backed status

- Keep publishing status in a content DB (`content_plan_slots.status`, `content_plan_images.status`). A successful API response alone is not proof the client rendered the post — read the post back through the API (`wall.get` for the group), then verify attachment types in a real client.
