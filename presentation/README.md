# Presentation

The defense deck for «Лаборатория протоколов» (UMIRHack 2026, case #02,
Мадригал). The deck is authored as a single self-contained HTML file and printed
to PDF and PPTX; the visualisations and the GUI screenshots are built from the
repository's own code. Every number is from `docs/METRICS.md`.

## Files

| Path | What it is |
| --- | --- |
| `Презентация Madrigal Protocol Lab.html` | the deck source, 14 slides, dark theme, all images inlined |
| `Презентация Madrigal Protocol Lab (светлая).html` | the same deck in the light theme |
| `slide.pdf` | the printed export, 14 pages, 2560×1440 |
| `slide-light.pdf` | the same deck exported for a washed-out projector |
| `slide.pptx` | the deck as a PPTX, one full-bleed image per slide, zip timestamps pinned to 1980-01-01 |
| `slide-light.pptx` | the light variant as a PPTX |
| `screenshots/` | 11 real GUI captures at 1920×1080 (`generate_screenshots.py`) |
| `assets/` | 8 branded SVG visualisations, dark and light, plus PNG copies |
| `assets/madrigal-logo.png` | the case owner's «Мадригал» wordmark, shown on the cover and closing slides |
| `assets/madrigal-mark.png` | the square monogram used as a watermark |
| `assets/brand/` | three abstract background textures from the case owner's site |
| `public/` | assets the deck serves: fonts, logo, QR codes, member photos |
| `public/screencast-poster.png` | a spare poster frame baked from `screencast.mp4` (not shown on any slide) |
| `defense_script.md` | the 5- and 10-minute speaker routes, one section per slide |
| `Q_and_A.md` | the questions asked after the talk and the prepared answers |
| `VIDEO.md` | shot list for the reserve screen recording |
| `screencast.mp4` | the reserve recording of a full run (2:22, H.264, no sound) |
| `record_demo.py` | drives the real window through the demo scenario for the recording |
| `screencast.py` | the same driver on a real (xvfb) display so `ffmpeg -f x11grab` can record it |
| `generate_screenshots.py` | renders the eleven window captures offscreen |
| `make_assets.py` | panel crops, QR codes and the round member photos |
| `make_brand.py` | builds the «Мадригал» wordmark and monogram |
| `generate_qr.py` | writes the repository and release QR codes |

## Building the deck

The HTML is the source of truth. Both PDFs are printed from it with headless
Chromium at a 2560×1440 page size; the PPTX packages one rendered page per slide
with python-pptx. The dark theme is the HTML as authored; the light theme is a
recolour of the same markup with the brand marks left dark and the surfaces
lifted, so the layout and the copy are identical between the two.

```bash
# print each theme to PDF (Chromium must be on PATH)
chromium --headless --no-pdf-header-footer --print-to-pdf=slide.pdf \
  "Презентация Madrigal Protocol Lab.html"
chromium --headless --no-pdf-header-footer --print-to-pdf=slide-light.pdf \
  "Презентация Madrigal Protocol Lab (светлая).html"
```

## Regenerate the assets

```bash
# real GUI screenshots (1920x1080)
QT_QPA_PLATFORM=offscreen python -m presentation.generate_screenshots

# panel crops, QR codes and the round member photos
python -m presentation.make_assets

# the «Мадригал» wordmark and monogram
python -m presentation.make_brand
```

## Notes

- The deck is one file: fonts, logos, QR codes, screenshots and charts are all
  inlined as `data:` URIs, so it opens and prints without a web server and
  without the rest of the repository.
- Fonts (Tektur, Montserrat, JetBrains Mono) are bundled under `public/fonts/`
  and shipped in the HTML, so a machine without the families installed still
  shows the deck's own typefaces.
- The two member photos on slide 2 come from `assets/team/`; `make_assets.py`
  crops them to the round `public/avatar_*_round.png` the slide uses.
- The deck uses the Madrigal palette: background `#131516`, panels `#1D1D1D`,
  accent `#6D071F`, text `#E0E0E0`, secondary `#9F9F9F`; corners 4 px. The light
  theme lifts the surfaces and keeps the accent.
- The PPTX pins its zip timestamps to 1980-01-01, so two builds of the same deck
  are byte-identical and the file does not churn in git.
