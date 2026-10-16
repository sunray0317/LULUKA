# LULUKA GitHub hosting

The public site is built from `scripts/public-files.json` and deployed by GitHub Pages.
Public images and fonts are under `brands/assets/vendor/`; no published HTML, CSS,
JavaScript, image or font requires Supabase. Original font license files are included.
`docs/public-assets-localized.json` records the 76 downloaded public objects and their
SHA-256 hashes. No private bucket was copied into this public repository.

The gold homepage wordmark is `brands/assets/luluka-gold-wordmark.png`, a transparent
PNG extracted using the built-in image tool. Edit prompt: remove only the black
background; preserve LULUKA lettering, gold texture, spacing and all serif/tail shapes.

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
