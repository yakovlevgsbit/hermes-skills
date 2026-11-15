#!/usr/bin/env python3
"""Publish a video to Instagram/TikTok/YouTube via Upload-Post API.

Reads UPLOAD_POST_API_KEY from env or .env file (override: UPLOAD_POST_ENV_PATH, UPLOAD_POST_USER).
Prints a JSON result to stdout; exits 0 if at least one platform succeeded.
"""
import argparse, hashlib, json, os, sys, time, urllib.request, urllib.error, uuid

API = "https://api.upload-post.com"
ENV_PATH = os.environ.get("UPLOAD_POST_ENV_PATH", ".env")
DEFAULT_USER = os.environ.get("UPLOAD_POST_USER", "")  # required: set env or pass --user


def load_key():
    key = os.environ.get("UPLOAD_POST_API_KEY")
    if key:
        return key
    try:
        with open(ENV_PATH) as f:
            for line in f:
                if line.startswith("UPLOAD_POST_API_KEY="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass
    sys.exit("ERROR: UPLOAD_POST_API_KEY not found in env or " + ENV_PATH)


def api_request(method, path, key, fields=None, files=None, headers=None, timeout=120):
    """Minimal multipart/form-data or GET request with stdlib only."""
    url = API + path
    hdrs = {"Authorization": "Apikey " + key}
    if headers:
        hdrs.update(headers)
    data = None
    if method == "POST":
        boundary = "----up" + uuid.uuid4().hex
        body = bytearray()
        for name, val in (fields or {}).items():
            for v in (val if isinstance(val, list) else [val]):
                body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{v}\r\n'.encode()
        for name, (fname, content, ctype) in (files or {}).items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{fname}"\r\nContent-Type: {ctype}\r\n\r\n'.encode()
            body += content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        data = bytes(body)
        hdrs["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"success": False, "message": f"HTTP {e.code}"}
    except Exception as e:
        return 0, {"success": False, "message": str(e)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, help="Local file path or public URL")
    p.add_argument("--title", required=True, help="Caption (IG/TikTok) / fallback title")
    p.add_argument("--youtube-title")
    p.add_argument("--youtube-description")
    p.add_argument("--platforms", nargs="+", default=["instagram", "tiktok", "youtube"])
    p.add_argument("--user", default=DEFAULT_USER)
    p.add_argument("--schedule", help="ISO-8601 datetime for scheduled publish")
    p.add_argument("--timezone", default="Europe/Moscow")
    p.add_argument("--tiktok-mode", choices=["direct", "draft"], default="draft")
    p.add_argument("--instagram-title", help="Specific Instagram caption/title; falls back to --title")
    p.add_argument("--media-type", choices=["REELS", "STORIES"], default="REELS")
    p.add_argument("--share-mode", choices=["CUSTOM", "TRIAL_REELS_SHARE_TO_FOLLOWERS_IF_LIKED", "TRIAL_REELS_DONT_SHARE_TO_FOLLOWERS"], default="CUSTOM")
    p.add_argument("--share-to-feed", choices=["true", "false"], help="Regular Reels only; ignored for Trial Reels")
    p.add_argument("--cover-url", help="Public URL for Instagram cover image")
    p.add_argument("--cover-image", help="Local JPEG cover image for Instagram")
    p.add_argument("--ai-generated", action="store_true")
    p.add_argument("--wait", action="store_true", help="Poll status until finished")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--timeout-min", type=int, default=12)
    a = p.parse_args()

    key = load_key()
    if not a.dry_run and not a.user:
        sys.exit("ERROR: Upload-Post profile is required: pass --user <profile> or set UPLOAD_POST_USER")

    if a.dry_run:
        ok_video = a.video.startswith("http") or os.path.isfile(a.video)
        st, acc = api_request("GET", "/api/uploadposts/users", key)
        accts = {}
        for prof in acc.get("profiles", []):
            for plat, accd in (prof.get("social_accounts") or {}).items():
                if isinstance(accd, dict):
                    accts[plat] = {"handle": accd.get("handle"), "reauth": accd.get("reauth_required")}
        print(json.dumps({"dry_run": True, "video_ok": ok_video, "accounts": accts,
                          "platforms_requested": a.platforms}, ensure_ascii=False, indent=2))
        return

    fields = {
        "user": a.user,
        "platform[]": a.platforms,
        "title": a.title,
        "async_upload": "true",
    }
    yt_title = a.youtube_title or a.title.split("\n")[0][:100]
    if "instagram" in a.platforms:
        fields["instagram_title"] = a.instagram_title or a.title
        fields["media_type"] = a.media_type
        fields["share_mode"] = a.share_mode
        if a.share_to_feed is not None:
            fields["share_to_feed"] = a.share_to_feed
        if a.cover_url:
            fields["cover_url"] = a.cover_url
    if "youtube" in a.platforms:
        fields["youtube_title"] = yt_title
        fields["youtube_description"] = a.youtube_description or a.title
    if "tiktok" in a.platforms and a.tiktok_mode == "draft":
        fields["post_mode"] = "MEDIA_UPLOAD"
    if a.ai_generated:
        fields["is_ai_generated"] = "true"
    if a.schedule:
        fields["scheduled_date"] = a.schedule
        fields["timezone"] = a.timezone
        fields.pop("async_upload", None)

    files = None
    idem_src = a.video + a.title
    if a.video.startswith("http"):
        fields["video"] = a.video
    else:
        if not os.path.isfile(a.video):
            sys.exit(f"ERROR: file not found: {a.video}")
        with open(a.video, "rb") as f:
            content = f.read()
        files = {"video": (os.path.basename(a.video), content, "video/mp4")}
        idem_src = hashlib.sha1(content).hexdigest() + a.title
    if a.cover_image:
        if not os.path.isfile(a.cover_image):
            sys.exit(f"ERROR: cover image not found: {a.cover_image}")
        with open(a.cover_image, "rb") as f:
            cover_content = f.read()
        if files is None:
            files = {}
        files["cover_image"] = (os.path.basename(a.cover_image), cover_content, "image/jpeg")

    idem = hashlib.sha1(idem_src.encode()).hexdigest()[:32]
    status, resp = api_request("POST", "/api/upload", key, fields=fields, files=files,
                               headers={"Idempotency-Key": idem}, timeout=300)
    out = {"http_status": status, "initial_response": resp}

    request_id = resp.get("request_id")
    job_id = resp.get("job_id")
    if a.schedule:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    if a.wait and (request_id or job_id):
        q = f"request_id={request_id}" if request_id else f"job_id={job_id}"
        deadline = time.time() + a.timeout_min * 60
        final = None
        while time.time() < deadline:
            time.sleep(15)
            st, sresp = api_request("GET", f"/api/uploadposts/status?{q}", key)
            final = sresp
            results = (sresp or {}).get("results") or {}
            # API may return results as list of per-platform dicts
            if isinstance(results, list):
                results = {str(r.get("platform", i)): r for i, r in enumerate(results)
                           if isinstance(r, dict)}
            status_str = str(sresp.get("status", "")).lower()
            done = status_str in ("completed", "success", "finished", "failed", "error")
            if results and all(
                isinstance(r, dict) and ("success" in r or "error" in r or "url" in r)
                for r in results.values()):
                done = True
            if done:
                break
        out["final_status"] = final
        results = (final or {}).get("results") or {}
        if isinstance(results, list):
            results = {str(r.get("platform", i)): r for i, r in enumerate(results)
                       if isinstance(r, dict)}
        def _summary_line(plat, r):
            if not isinstance(r, dict):
                return "FAIL"
            if r.get("success") and not r.get("fallback_to_inbox"):
                return "OK " + str(r.get("url") or r.get("post_url") or "")
            if r.get("fallback_to_inbox"):
                return "INBOX_DRAFT"
            status = str(r.get("status") or (final or {}).get("status") or "").lower()
            if status in {"processing", "queued", "pending", "running", "scheduled"}:
                return "PENDING"
            return "FAIL " + str(r.get("error") or r.get("error_message") or "unknown")

        out["summary"] = {plat: _summary_line(plat, r) for plat, r in results.items()}
    print(json.dumps(out, ensure_ascii=False, indent=2))

    summary = out.get("summary") or {}
    if summary and not any(v.startswith("OK") for v in summary.values()):
        if any(v == "PENDING" for v in summary.values()):
            sys.exit(3)
        sys.exit(2)


if __name__ == "__main__":
    main()
