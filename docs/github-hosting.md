# LULUKA GitHub hosting

The public site is built from `scripts/public-files.json` and deployed by GitHub Pages.
Public images and fonts are under `brands/assets/vendor/`; no published HTML, CSS,
JavaScript, image or font requires Supabase. Original font license files are included.
`docs/public-assets-localized.json` records the 76 downloaded public objects and their
SHA-256 hashes. No private bucket was copied into this public repository.

The approved homepage wordmark is `brands/assets/luluka-classic-wordmark-20261017.png`
(1400 x 229 RGBA). It is a transparent extraction of the selected upright-KA concept,
made with the built-in image tool; the old wordmark remains in Git for rollback.
Extraction prompt: remove only the black/brown background and letter counters;
preserve the selected six letter outlines, kerning, flat serif A top, short K leg,
warm honey/champagne faces and delicate highlights. No redesign or recoloring.
Transparent canvas was trimmed and resized for delivery without further recoloring.
The header is fixed at the viewport's top center with no black bar, blur or border.
The logo is up to 220px on desktop and 180px on mobile, with no color filter.
Safe-area-aware main padding keeps the first cards clear at initial load. Only the
logo link receives pointer input, so the rest of the transparent header passes through.

Private source artwork and database exports belong only in the separate private
`sunray0317/LULUKA-private-archive` repository. It has no Pages deployment. Supabase
must remain intact until every private object and record has been exported and checked.

## Build and validate (CMD, bash or other shell)

```text
python -X utf8 scripts/build_public.py
python -X utf8 scripts/check_public.py
```

Windows may lack permission to create a test symlink. The test reports that limitation;
GitHub's Linux build always executes the symlink check. The actual deployment allowlist,
all local links, SEO metadata and vendored object hashes are still checked on Windows.

Development can use any shell. Publishing through the connected GitHub tool does not
require Windows Git Credential Manager. Never put account tokens in repository files.
