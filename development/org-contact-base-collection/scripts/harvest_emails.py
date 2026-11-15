"""Harvest emails from organization websites (stage 2 of a contact base).

Usage:
    python3 harvest_emails.py domains.txt          # one domain/URL per line
    python3 harvest_emails.py orgs.csv --column "Веб-сайт 1"

Prints a per-site result and a final hit rate. Emails are extracted from the
homepage plus same-host contact/about pages. Junk matches (library and asset
strings) are filtered out.

Designed for large lists: thread-pooled, per-request timeout, tolerant of
unreachable hosts. For 20k+ hosts run it in the background and write results to
a file as they land.
"""
import argparse
import concurrent.futures as cf
import csv
import re
from urllib.parse import urljoin, urlparse

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# library / asset / placeholder matches that pass the regex but are not addresses
BAD_SUBSTR = ("example.", "sentry", "@2x", "wixpress", "u003", "domain.com",
              "yourmail", "mail@mail")
BAD_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js",
           ".woff", ".woff2", ".ico", ".json", ".xml")
CONTACT_HINTS = ("contact", "kontakt", "контакт", "about", "o-nas", "o_nas",
                 "info", "clinic", "klinika")


def norm(u: str) -> str:
    u = u.strip()
    if not u:
        return ""
    if not u.startswith("http"):
        u = "https://" + u
    return u.rstrip("/")


def fetch(url: str, timeout: int = 10) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout,
                         allow_redirects=True)
        if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
            return r.text
    except Exception:
        pass
    return ""


def emails_from(html: str) -> set:
    out = set()
    for m in EMAIL_RE.findall(html or ""):
        e = m.strip().lower().strip(".,;:")
        if e.count("@") != 1 or len(e) > 60:
            continue
        if any(b in e for b in BAD_SUBSTR):
            continue
        if e.endswith(BAD_EXT):
            continue
        out.add(e)
    return out


def harvest(site: str) -> tuple:
    base = norm(site)
    if not base:
        return site, [], "empty"
    html = fetch(base)
    if not html:
        return site, [], "unreachable"
    found = emails_from(html)
    links = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
    cands = []
    host = urlparse(base).netloc
    for h in links:
        if any(x in h.lower() for x in CONTACT_HINTS):
            full = urljoin(base, h)
            if urlparse(full).netloc == host and full not in cands:
                cands.append(full)
    for u in cands[:3]:
        found |= emails_from(fetch(u, 8))
    return site, sorted(found), "ok" if found else "no_email"


def load_targets(path: str, column: str | None) -> list:
    if path.endswith(".csv") and column:
        with open(path, encoding="utf-8-sig") as fh:
            return [r.get(column, "") for r in csv.DictReader(fh) if r.get(column)]
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="txt of domains/URLs, or a CSV")
    ap.add_argument("--column", help="CSV column holding the website")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", help="write TSV results here")
    args = ap.parse_args()

    targets = load_targets(args.input, args.column)
    ok = 0
    uniq = set()
    rows = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for site, mails, status in ex.map(harvest, targets):
            rows.append((site, ";".join(mails), status))
            if mails:
                ok += 1
                uniq |= set(mails)
                print(f"OK   {site:<45} {', '.join(mails[:3])}")
            else:
                print(f"MISS {site:<45} ({status})")

    n = max(len(targets), 1)
    print(f"\n=== RESULT ===\nsites: {n} | with email: {ok} ({ok*100//n}%) "
          f"| unique emails: {len(uniq)}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("site\temails\tstatus\n")
            for site, mails, status in rows:
                fh.write(f"{site}\t{mails}\t{status}\n")
        print(f"written: {args.out}")


if __name__ == "__main__":
    main()
