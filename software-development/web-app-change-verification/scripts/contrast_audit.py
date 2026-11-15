#!/usr/bin/env python3
"""Contrast audit of a live page: report every text element below a WCAG ratio.

Why this exists: a dark theme can be applied and still render dark-on-dark wherever an
element reads a CSS variable that was never re-declared, or carries a hardcoded colour.
A computed-style read of one element proves nothing about the rest of the page.

Run with the Hermes Playwright venv python. Example:

    /root/.hermes/installs/<hash>/environments/<hash>/venv/bin/python3.14 \
        contrast_audit.py https://host/page arrival output reports

Positional args are page ids passed to `showPage('<id>')` if the app exposes it; otherwise
omit them and audit the current screen only.
"""
import sys

AUDIT_JS = r"""(() => {
  const lum = (r, g, b) => {
    const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const parse = c => {
    const m = (c || '').match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(s => parseFloat(s.trim()));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  // walk up to the nearest ancestor with a non-transparent background
  const effBg = el => {
    let n = el;
    while (n && n !== document.documentElement) {
      const bg = parse(getComputedStyle(n).backgroundColor);
      if (bg && bg.a > 0.5) return bg;
      n = n.parentElement;
    }
    return { r: 11, g: 11, b: 11, a: 1 };
  };
  const out = [];
  const walk = el => {
    for (const ch of el.children) {
      const cs = getComputedStyle(ch);
      const txt = (ch.textContent || '').trim();
      if (txt && ch.children.length === 0 && cs.display !== 'none' && cs.visibility !== 'hidden') {
        const fg = parse(cs.color);
        if (fg) {
          const bg = effBg(ch);
          const l1 = lum(fg.r, fg.g, fg.b), l2 = lum(bg.r, bg.g, bg.b);
          const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
          if (ratio < 3.0) {
            out.push({
              text: txt.slice(0, 30), tag: ch.tagName.toLowerCase(),
              cls: String(ch.className || '').slice(0, 40),
              fg: cs.color, bg: `rgb(${bg.r},${bg.g},${bg.b})`,
              ratio: Math.round(ratio * 10) / 10,
            });
          }
        }
      }
      walk(ch);
    }
  };
  walk(document.body);
  return out;
})()"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    url = sys.argv[1]
    pages = sys.argv[2:]
    total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 420, "height": 1000})
        page.goto(url)
        page.wait_for_timeout(1800)

        targets = pages or [None]
        for pid in targets:
            if pid:
                page.evaluate(f"showPage('{pid}')")
                page.wait_for_timeout(2200)
            found = page.evaluate(AUDIT_JS)
            total += len(found)
            label = pid or "(current)"
            print(f"=== {label}: ratio < 3.0 -> {len(found)} ===")
            for x in found[:15]:
                print(f"   {x['ratio']:4.1f}  {x['text']:26s} fg={x['fg']:20s} bg={x['bg']}")

        browser.close()

    print(f"\nTOTAL low-contrast elements: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
