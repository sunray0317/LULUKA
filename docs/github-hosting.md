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
The transparent header is centered in normal document flow, with no black bar,
blur or border. It scrolls out of view rather than following the viewport.
The logo is up to 140px on desktop and 110px on mobile, with no color filter.
An alpha-masked CSS highlight adds a warm folded/refraction-like brush across only
the letters: a 5.6-second loop with a brief eased sweep and a quiet pause. No new
image or animation library is required. Both standard and WebKit mask properties
are provided; browsers without masking keep the static PNG. Reduced-motion users
receive the static wordmark without the sweep.
The header reserves its own height and accounts for the device top safe area;
there is no fixed-header spacer. Only the logo link receives pointer input.

Private source artwork and database exports belong only in the separate private
`sunray0317/LULUKA-private-archive` repository. It has no Pages deployment. Supabase
must remain intact until every private object and record has been exported and checked.

The homepage now shows only the five bronze rock-engraving theme cards (the former
second row). The ukiyo and pixel rows were removed from homepage markup after their
20 highest-resolution idle/feedback card images were exported as pixel-verified PNGs
to the owner's Downloads folder. Source assets remain in Git for recovery; the
homepage no longer preloads either removed row. Titles remain live HTML overlays.

Homepage delivery uses 320/640/960px WebP derivatives, not the source PNGs. All five
idle faces have real src/srcset attributes and can display without JavaScript; the
first face has a matching responsive preload. Desktop feedback loads only on pointer
or keyboard contact. Touch carousels never fetch unused feedback artwork. Original
PNGs remain unchanged. docs/bronze-card-delivery.json records measured file sizes.
The five 640px idle faces total 642,088 bytes versus 13,020,883 source PNG bytes (95%
less card-image data; this is not a measured page-load time). Rebuild derivatives
with scripts/optimize_bronze_cards.cjs after installing sharp or configuring NODE_PATH
to the bundled Node packages. The standard build does not need sharp.

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
