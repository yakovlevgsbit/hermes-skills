#!/usr/bin/env python3
"""web-design-check: measure a live web page's visual/a11y defects numerically.

Emits JSON on stdout and writes screenshots + an HTML report next to --out.
Numbers, not opinions: every finding carries the measured value.

Usage:
    python3 design_audit.py <url-or-file> [--out DIR] [--widths 375,768,1440]
"""
import argparse
import json
import os
import pathlib
import sys

MEASURE_JS = r"""
(() => {
  const out = {};
  const unmeasurable = [];
  // WCAG 2.2 SC 2.5.8 Target Size (Minimum) = AA = 24x24 CSS px.
  // SC 2.5.5 Target Size (Enhanced) = AAA = 44x44. Default to the AA bar;
  // using 44 as the default silently over-reports every real site.
  const TARGET_MIN = window.__TARGET_MIN__ || 24;

  // ---- contrast helpers ----
  function parseColor(c) {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(s => parseFloat(s.trim()));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  }
  function lum({r, g, b}) {
    const f = v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b);
  }
  function ratio(fg, bg) {
    const L1 = lum(fg), L2 = lum(bg);
    const [hi, lo] = L1 > L2 ? [L1, L2] : [L2, L1];
    return (hi + 0.05) / (lo + 0.05);
  }
  // Composite the whole ancestor background stack, bottom-up. Taking only the
  // first ancestor with alpha > 0 reports a false 1:1 on translucent chips.
  function effectiveBg(el) {
    const chain = [];
    let n = el;
    while (n && n.nodeType === 1) {
      const cs = getComputedStyle(n);
      // a gradient/image background cannot be resolved to one color
      if (cs.backgroundImage && cs.backgroundImage !== 'none' &&
          cs.backgroundImage.indexOf('gradient') !== -1) {
        chain.gradient = true;
      }
      const c = parseColor(cs.backgroundColor);
      if (c && c.a > 0) chain.push(c);
      if (n === document.documentElement) break;
      n = n.parentElement;
    }
    chain.push({ r: 255, g: 255, b: 255, a: 1 });
    let acc = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = chain.length - 1; i >= 0; i--) {
      const c = chain[i];
      acc = {
        r: c.r * c.a + acc.r * (1 - c.a),
        g: c.g * c.a + acc.g * (1 - c.a),
        b: c.b * c.a + acc.b * (1 - c.a),
        a: 1,
      };
    }
    acc.gradient = !!chain.gradient;
    return acc;
  }

  // ---- contrast on text nodes ----
  const contrast = [];
  const textEls = document.querySelectorAll('p, span, a, h1, h2, h3, h4, h5, h6, li, td, th, button, label, div');
  for (const el of textEls) {
    const direct = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (!direct) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) continue;

    const label = el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '');
    const snippet = el.textContent.trim().slice(0, 60);
    const fg = parseColor(cs.color);

    // Transparent text painted by a gradient (background-clip:text) has no
    // single color — reporting a ratio for it is a false positive.
    const clip = cs.webkitBackgroundClip || cs.backgroundClip;
    if (!fg || fg.a === 0 || clip === 'text') {
      unmeasurable.push({ selector: label, text: snippet, reason: 'gradient/transparent text' });
      continue;
    }
    const bg = effectiveBg(el);
    if (bg.gradient) {
      unmeasurable.push({ selector: label, text: snippet, reason: 'text over gradient/image background' });
      continue;
    }
    // composite a semi-transparent text color over its background
    const fgC = fg.a < 1
      ? { r: fg.r*fg.a + bg.r*(1-fg.a), g: fg.g*fg.a + bg.g*(1-fg.a), b: fg.b*fg.a + bg.b*(1-fg.a), a: 1 }
      : fg;
    const r = ratio(fgC, bg);
    const size = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight, 10) >= 700;
    // WCAG AA: 3.0 for large text (>=24px, or >=18.66px bold), else 4.5
    const large = size >= 24 || (bold && size >= 18.66);
    const need = large ? 3.0 : 4.5;
    if (r < need) {
      contrast.push({
        selector: label,
        text: snippet,
        ratio: Math.round(r * 100) / 100,
        required: need,
        fontSize: size,
        color: cs.color,
      });
    }
  }
  out.contrast = contrast;
  out.unmeasurable = unmeasurable;

  // ---- small tap targets ----
  // WCAG 2.5.8 exempts links rendered inline in a block of text; flagging those
  // buries the real findings (icon buttons, tiny controls).
  const small = [];
  const inlineExempt = [];
  for (const el of document.querySelectorAll('a, button, input[type=submit], input[type=button], [role=button]')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.width >= TARGET_MIN && r.height >= TARGET_MIN) continue;
    const label = el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '');
    const text = (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40);
    const parent = el.parentElement;
    const inlineInText = cs.display === 'inline' && parent &&
      parent.textContent.trim().length > (el.textContent || '').trim().length + 5;
    if (inlineInText) {
      inlineExempt.push({ selector: label, text: text, width: Math.round(r.width), height: Math.round(r.height) });
      continue;
    }
    small.push({
      selector: label, text: text,
      width: Math.round(r.width), height: Math.round(r.height),
    });
  }
  out.smallTargets = small;
  out.inlineLinksExempt = inlineExempt;

  // ---- images without alt ----
  const noAlt = [];
  for (const img of document.querySelectorAll('img')) {
    if (!img.hasAttribute('alt')) {
      noAlt.push({ src: (img.getAttribute('src') || '').slice(0, 80) });
    }
  }
  out.imagesWithoutAlt = noAlt;

  // ---- form controls without an accessible label ----
  const noLabel = [];
  for (const el of document.querySelectorAll('input:not([type=hidden]), select, textarea')) {
    const id = el.getAttribute('id');
    const hasLabel = (id && document.querySelector('label[for="' + id + '"]'))
      || el.closest('label')
      || el.getAttribute('aria-label')
      || el.getAttribute('aria-labelledby');
    if (!hasLabel) {
      noLabel.push({
        tag: el.tagName.toLowerCase(),
        inputType: el.getAttribute('type') || '',
        placeholder: el.getAttribute('placeholder') || '',
      });
    }
  }
  out.unlabeledControls = noLabel;

  // ---- overflow / layout ----
  const docW = document.documentElement.clientWidth;
  const scrollW = document.documentElement.scrollWidth;
  const overflowing = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width < 1) continue;
    if (r.right > docW + 1 || r.left < -1) {
      const cs = getComputedStyle(el);
      if (cs.position === 'fixed') continue;
      overflowing.push({
        selector: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : ''),
        right: Math.round(r.right),
        left: Math.round(r.left),
      });
    }
  }
  out.horizontalOverflow = { docWidth: docW, scrollWidth: scrollW, hasScroll: scrollW > docW + 1, elements: overflowing.slice(0, 20) };

  // ---- clipped / truncated text ----
  const clipped = [];
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    const hasText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 2);
    if (!hasText) continue;
    const clipX = el.scrollWidth > el.clientWidth + 1;
    const clipY = el.scrollHeight > el.clientHeight + 1;
    const hidden = cs.overflow === 'hidden' || cs.overflowX === 'hidden' || cs.overflowY === 'hidden';
    if (hidden && (clipX || clipY)) {
      clipped.push({
        selector: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : ''),
        text: el.textContent.trim().slice(0, 50),
        scrollW: el.scrollWidth, clientW: el.clientWidth,
        textOverflow: cs.textOverflow,
        clipped: true,
      });
    }
  }
  out.clippedText = clipped;

  // ---- focus visibility sample ----
  out.stats = {
    textElementsChecked: textEls.length,
    interactiveElements: document.querySelectorAll('a, button, input, select, textarea').length,
    images: document.querySelectorAll('img').length,
  };
  return out;
})()
"""


def run(url, outdir, widths, target_min=24):
    from playwright.sync_api import sync_playwright

    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
    shots = pathlib.Path(outdir) / "screenshots"
    shots.mkdir(exist_ok=True)

    results = {"url": url, "viewports": {}, "console": [], "failedRequests": [],
               "targetMin": target_min}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for w in widths:
            ctx = browser.new_context(viewport={"width": w, "height": 900})
            page = ctx.new_page()
            console, failed = [], []
            page.on("console", lambda m: console.append({"type": m.type, "text": m.text[:200]})
                    if m.type in ("error", "warning") else None)
            page.on("requestfailed", lambda r: failed.append({"url": r.url[:120], "failure": str(r.failure)[:80]}))
            page.on("response", lambda r: failed.append({"url": r.url[:120], "status": r.status})
                    if r.status >= 400 else None)

            page.goto(url, wait_until="load", timeout=30000)
            page.wait_for_timeout(600)
            page.evaluate(f"window.__TARGET_MIN__ = {target_min}")
            measured = page.evaluate(MEASURE_JS)
            shot = shots / f"viewport-{w}.png"
            page.screenshot(path=str(shot), full_page=True)
            measured["screenshot"] = str(shot)
            results["viewports"][w] = measured
            if w == widths[0]:
                results["console"] = console[:30]
                results["failedRequests"] = failed[:30]
            ctx.close()
        browser.close()

    # aggregate — spread the payload FIRST, then set type/severity, so a payload
    # key named "type" (console entries, form controls) cannot clobber them.
    findings = []
    for w, m in results["viewports"].items():
        for c in m["contrast"]:
            findings.append({**c, "type": "contrast", "viewport": w,
                             "severity": "high" if c["ratio"] < 3 else "medium"})
        for s in m["smallTargets"]:
            findings.append({**s, "type": "small-tap-target", "viewport": w, "severity": "medium"})
        for i in m["imagesWithoutAlt"]:
            findings.append({**i, "type": "image-no-alt", "viewport": w, "severity": "medium"})
        for u in m["unlabeledControls"]:
            findings.append({**u, "type": "unlabeled-control", "viewport": w, "severity": "high"})
        for cl in m["clippedText"]:
            findings.append({**cl, "type": "clipped-text", "viewport": w, "severity": "medium"})
        if m["horizontalOverflow"]["hasScroll"]:
            findings.append({**{k: v for k, v in m["horizontalOverflow"].items() if k != "elements"},
                             "type": "horizontal-overflow", "viewport": w, "severity": "high"})
    for e in results["console"]:
        if e["type"] == "error":
            findings.append({**e, "type": "console-error", "severity": "high"})
    for f in results["failedRequests"]:
        findings.append({**f, "type": "failed-request", "severity": "high"})

    results["findings"] = findings
    results["summary"] = {
        "total": len(findings),
        "byType": {t: sum(1 for f in findings if f["type"] == t)
                   for t in sorted({f["type"] for f in findings})},
        "unmeasurable": sum(len(m.get("unmeasurable", [])) for m in results["viewports"].values()),
        "inlineLinksExempt": sum(len(m.get("inlineLinksExempt", [])) for m in results["viewports"].values()),
    }
    out = pathlib.Path(outdir)
    json.dump(results, open(out / "audit.json", "w"), ensure_ascii=False, indent=1)
    (out / "report.md").write_text(render_report(results), encoding="utf-8")
    return results


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

TYPE_LABEL = {
    "contrast": "Недостаточный контраст текста (WCAG AA)",
    "small-tap-target": "Кликабельная зона меньше нормы WCAG (2.5.8/2.5.5)",
    "image-no-alt": "Изображение без alt",
    "unlabeled-control": "Поле формы без label",
    "clipped-text": "Текст обрезан без многоточия",
    "horizontal-overflow": "Горизонтальный скролл / вылезание за вьюпорт",
    "console-error": "Ошибка в JS-консоли",
    "failed-request": "Проваленный сетевой запрос",
}


def render_report(r):
    s = r["summary"]
    lines = [
        "# Проверка дизайна / вёрстки",
        "",
        f"**Страница:** {r['url']}",
        f"**Вьюпорты:** {', '.join(str(w) for w in r['viewports'])}",
        f"**Находок:** {s['total']}",
        "",
        "## Сводка по типам",
        "",
        "| Тип | Кол-во |",
        "|---|---|",
    ]
    for t, n in s["byType"].items():
        lines.append(f"| {TYPE_LABEL.get(t, t)} | {n} |")

    lines += ["", "## Находки", ""]
    findings = sorted(r["findings"], key=lambda f: (SEVERITY_ORDER.get(f.get("severity"), 9),
                                                    str(f.get("type"))))
    if not findings:
        lines.append("Находок нет — по измеренным критериям страница чистая.")
    for i, f in enumerate(findings, 1):
        vp = f.get("viewport")
        head = f"### {i}. [{f.get('severity','?').upper()}] {TYPE_LABEL.get(f['type'], f['type'])}"
        if vp:
            head += f" — {vp}px"
        lines.append(head)
        lines.append("")
        if f["type"] == "contrast":
            lines.append(f"- Селектор: `{f['selector']}`")
            lines.append(f"- Текст: «{f['text']}»")
            lines.append(f"- Контраст **{f['ratio']}:1**, требуется {f['required']}:1 (размер {f['fontSize']}px)")
        elif f["type"] == "small-tap-target":
            lines.append(f"- Селектор: `{f['selector']}`")
            lines.append(f"- Размер **{f['width']}×{f['height']}px**, требуется ≥{f.get('targetMin', r.get('targetMin', 24))}×{f.get('targetMin', r.get('targetMin', 24))}px")
        elif f["type"] == "image-no-alt":
            lines.append(f"- src: `{f.get('src','')}`")
        elif f["type"] == "unlabeled-control":
            lines.append(f"- Элемент: `{f.get('tag')}` type=`{f.get('inputType','')}` placeholder=«{f.get('placeholder')}»")
        elif f["type"] == "clipped-text":
            lines.append(f"- Селектор: `{f['selector']}`")
            lines.append(f"- Текст: «{f['text']}»")
            lines.append(f"- scrollWidth {f['scrollW']} > clientWidth {f['clientW']}, overflow скрыт")
        elif f["type"] == "horizontal-overflow":
            lines.append(f"- Ширина документа {f['docWidth']}px, scrollWidth {f['scrollWidth']}px")
        elif f["type"] in ("console-error", "failed-request"):
            lines.append(f"- {f.get('text') or f.get('url')}")
        lines.append("")

    lines += ["## Скриншоты", ""]
    for w, m in r["viewports"].items():
        lines.append(f"- {w}px: `{m.get('screenshot','')}`")

    # Honest boundaries: what the script refused to judge, and why.
    unmeas = []
    for w, m in r["viewports"].items():
        for u in m.get("unmeasurable", []):
            unmeas.append((w, u))
    if unmeas:
        lines += ["", "## Не измерено (нужен глаз человека)", "",
                  "Эти элементы скрипт намеренно пропустил — цвет фона под ними "
                  "не сводится к одному значению, поэтому любая цифра была бы ложной:", ""]
        seen = set()
        for w, u in unmeas:
            k = (u.get("selector"), u.get("reason"))
            if k in seen:
                continue
            seen.add(k)
            lines.append(f"- `{u.get('selector')}` — {u.get('reason')} — «{u.get('text','')[:40]}»")

    exempt = r["summary"].get("inlineLinksExempt", 0)
    if exempt:
        lines += ["", f"Плюс {exempt} инлайн-ссылок в тексте пропущено: WCAG 2.5.8 "
                      "делает для них исключение по размеру зоны клика.", ""]

    lines += ["", "## Что НЕ проверено", "",
              "Скрипт измеряет перечисленные критерии и ничего больше: он не судит",
              "о вкусе, композиции, иерархии, читаемости текста и качестве картинок.",
              "Это смотрит человек. Отсутствие находок ≠ хороший дизайн.",
              ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="design-audit-output")
    ap.add_argument("--widths", default="375,768,1440")
    ap.add_argument("--target-min", type=int, default=24,
                    help="min tap target in CSS px: 24 = WCAG AA (2.5.8), 44 = AAA (2.5.5)")
    a = ap.parse_args()
    widths = [int(x) for x in a.widths.split(",")]
    r = run(a.url, a.out, widths, target_min=a.target_min)
    print(json.dumps(r["summary"], ensure_ascii=False, indent=1))
    print(f"\naudit.json + screenshots -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
