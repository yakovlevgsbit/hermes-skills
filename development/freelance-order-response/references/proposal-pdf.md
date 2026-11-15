# Client proposal PDF (КП) from a scope+price plan

When the client asks for the plan «в PDF», turn the scope/price table you
already wrote into a sendable document. Keep it a generated artifact, not
hand-typed layout.

## Recipe

1. **Write the generator to a file, then run it.** Do not inline a long
   multi-table reportlab script into a shell heredoc — a single mismatched
   bracket aborts the whole run and the error points at the wrong line. Use
   `write_file` for `generate_pdf.py`, then run it with `terminal`. Re-running
   after an edit is one command.
2. **Register a Cyrillic-capable font first.** reportlab's built-in Helvetica
   has no Cyrillic glyphs; without registration the text renders as blanks or
   boxes and the failure is silent in the PDF. Register DejaVu at the top:

   ```python
   from reportlab.pdfbase import pdfmetrics
   from reportlab.pdfbase.ttfonts import TTFont
   pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
   pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
   ```

   Then set `fontName='DejaVu'` (or `'DejaVu-Bold'`) on **every** ParagraphStyle
   and TableStyle — one style left at the default reintroduces the blank text.
3. **Build the document the client reads, not the one you wrote.** Structure that
   works for a КП: title page (project / company / competitor / date) → short
   «О проекте» → competitor comparison table → one section per stage with its
   cost table → totals table (one-off vs monthly, clearly separated) → discounts
   and terms → timeline with expected result per period → recommendation tiers
   (minimum / optimal / constrained budget) → contacts.
4. **Every stage gets its own cost table** with a bold total row, and the totals
   page repeats them. A client forwards one page; each page must stand alone.
5. **Write to the workspace dir and deliver with `MEDIA:`.** The path goes in
   the reply; the platform renders it as a downloadable card.

## Pitfalls

- **No font registration → silent blank Cyrillic.** See above; it is the first
  thing to check when a generated PDF «looks empty».
- **Missing `fontName` on one style.** Per-style, not document-wide. Sweep all
  styles after the first fix.
- **Prices in the wrong currency.** A KZ client reads tenge; give rubles only as
  a note, and state the rate used (see the parent skill's pricing section).
- **A single flat price for everything.** Split one-off work from monthly
  retainer explicitly — the client's decision is which tier to buy, and a flat
  number hides it.
- **Inline heredoc for a long script.** Write the file; the bracket error is
  unreadable otherwise.
