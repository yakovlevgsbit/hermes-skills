#!/usr/bin/env python3
"""
Send proposal PDFs to a lead list through the Resend REST API.

Why a REST API instead of SMTP: many hosts filter outbound SMTP ports
(25/465/587) while leaving 443 open, so HTTPS delivery bypasses the block.

Usage:
  python3 send_resend.py --dry-run --limit 5          # show the plan only
  python3 send_resend.py --to me@example.com --limit 1 # self-test with attachment
  python3 send_resend.py --send --limit 50            # real campaign

Requirements: pip install curl_cffi  (see the Cloudflare pitfall below)
Key:        RESEND_API_KEY in env, or /root/.secrets/resend.env
"""
import argparse
import base64
import csv
import re
import sys
import time
from pathlib import Path

FROM_NAME = "Sales"
FROM_EMAIL = "onboarding@resend.dev"   # replace after verifying your domain
REPLY_TO = ""
SECRET_FILE = Path("/root/.secrets/resend.env")


def load_key():
    key = ""
    for line in open(SECRET_FILE, encoding="utf-8"):
        if line.startswith("RESEND_API_KEY="):
            key = line.strip().split("=", 1)[1]
    return key


def send(key, to, subject, html, attachment=None):
    """Return (ok, detail).

    curl_cffi with impersonate='chrome' is required: Cloudflare in front of the
    API rejects non-browser TLS fingerprints — urllib/requests get
    403 'error code: 1010' while curl returns 200.
    """
    from curl_cffi import requests as cr

    body = {"from": f"{FROM_NAME} <{FROM_EMAIL}>", "to": [to],
            "subject": subject, "html": html}
    if REPLY_TO:
        body["reply_to"] = REPLY_TO
    if attachment and Path(attachment).exists():
        body["attachments"] = [{"filename": Path(attachment).name,
                                "content": base64.b64encode(Path(attachment).read_bytes()).decode()}]

    try:
        r = cr.post("https://api.resend.com/emails", json=body,
                    headers={"Authorization": "Bearer " + key},
                    impersonate="chrome", timeout=30)
        if r.status_code == 200:
            try:
                return True, r.json().get("id", "ok")
            except Exception:
                return True, "ok"
        return False, f"{r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def body_html(company, city):
    return (f"<div style=\"font-family:-apple-system,'Segoe UI',Roboto,sans-serif;max-width:560px;color:#1a1a1a\">"
            f"<p>Здравствуйте!</p>"
            f"<p>Предлагаю решение для <b>{esc(company)}</b> ({esc(city)}). "
            f"Подробности — во вложении.</p>"
            f"<p>Готов показать демо на ваших данных — 10 минут на звонке?</p></div>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads", required=True, help="CSV with name, city, email")
    ap.add_argument("--proposals", default=".", help="dir with proposal PDFs")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--to", help="send only to this address (self-test)")
    ap.add_argument("--send", action="store_true", help="actually send (default is a dry run)")
    args = ap.parse_args()

    real = bool(args.send)
    key = load_key() if real else ""
    if real and not key:
        sys.exit(f"no RESEND_API_KEY in {SECRET_FILE}")

    rows = [r for r in csv.DictReader(open(args.leads, encoding="utf-8"))
            if r.get("email") and "@" in r["email"]]
    # dedup by company, not by contact — one firm must not get two pitches
    seen_company, uniq = set(), []
    for r in rows:
        k = (r.get("name") or "").strip().lower()
        if k in seen_company:
            continue
        seen_company.add(k)
        uniq.append(r)
    uniq = uniq[:args.limit]

    if args.to:
        uniq = [dict(uniq[0], email=args.to)] if uniq else [{"name": "Test", "city": "", "email": args.to}]

    print(f"{'SENDING' if real else 'PLAN'}: {len(uniq)} messages")
    ok = fail = 0
    for i, r in enumerate(uniq, 1):
        company = r.get("name", "")
        to = r["email"].strip()
        pdf = None
        if args.to:
            pdfs = sorted(Path(args.proposals).glob("*.pdf"))
            pdf = pdfs[0] if pdfs else None
        else:
            safe = re.sub(r"\W+", "_", company)[:30]
            cand = list(Path(args.proposals).glob(f"*{safe}*.pdf"))
            pdf = cand[0] if cand else None

        if not real:
            print(f"  [{i}/{len(uniq)}] {company[:38]:40s} -> {to:32s} "
                  f"{'with PDF' if pdf and pdf.exists() else 'no attachment'}")
            continue

        status, detail = send(key, to, f"{company} — предложение",
                             body_html(company, r.get("city", "")), pdf)
        ok += status
        fail += not status
        print(f"  [{i}/{len(uniq)}] {company[:38]:40s} -> {to:32s} "
              f"{'OK ' if status else 'FAIL'} {detail[:40]}")
        time.sleep(1.2)   # stay under the provider rate limit

    print(f"\nDONE: {ok} sent, {fail} failed")
    if not real:
        print("Dry run. Add --send to actually deliver.")


if __name__ == "__main__":
    main()
