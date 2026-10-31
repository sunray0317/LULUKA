# Visual-design updates

`data/visual-design-projects.json` is the source of project-to-SDG associations.
Use only confirmed associations. The overview keeps all 17 icons colored;
project pages color the goals in that project's `goals` array.

The sticky header has 18 square tiles in one row, without gaps; small screens scroll horizontally.
The first is a black-and-gold 0/menu tile linking to the visual-design overview;
the other 17 retain their goal colors, links and hover/press feedback.

Each icon is a normal link to `/visual-design/sdgs/<number>/`. The build creates
all 17 pages, with every matching project presented using the overview artwork rows.
A category colors only its own selected goal, even when no projects match.
The goal icon appears before its heading. Empty categories show no placeholder message.
No popup or click-handler JavaScript is needed.

When adding a project:

1. Add its source HTML, original artwork and reviewed public files to the allowlist.
2. Add its title, organization, URL, cover and confirmed goals to the registry.
3. Run `node scripts/prepare_portfolio_media.cjs` locally. It uses Sharp; set
   `LULUKA_SHARP_MODULE` if the module is installed in a different location.
   Original files remain unchanged; responsive WebP files and their manifest
   are generated under `brands/assets/portfolio-media/` and `docs/`.
4. Run `python scripts/build_public.py`, then `python scripts/check_public.py`.
   The public build regenerates the headers, category pages, responsive image
   tags, high-priority first-image preload and content-based CSS versions.
5. Commit the sources, registry, generated pages, delivery manifest, image
   derivatives and updated allowlist. The GitHub Pages build needs only Python.

The performance report measures estimated image request bytes for selected
viewport/DPR combinations. It is not a browser paint-time or real network test.
