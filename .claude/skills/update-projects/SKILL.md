---
name: update-projects
description: Refresh the project list on Alec's homepage (index.html) from GitHub. Use when asked to update the homepage/projects page, check what changed in his projects, or pick up new project sites, releases or repos.
---

# Update the projects on the homepage

The projects are the `<article class="proj">` blocks in `index.html`; the README explains their `data-*` attributes.

## 1. Survey

```bash
python3 .claude/skills/update-projects/survey.py index.html   # --days N widens the "not on the page" window (default 120)
```

Read-only. For each project it prints the page's values, what GitHub says now, sites found (repo homepage field and GitHub Pages, probed for HTTP 200), the latest release, the human commits since the page's `data-updated`, and a `CHANGES:` line. It ends with recently pushed public repos missing from the page.

## 2. Apply the mechanical changes

- `data-updated`, `data-commits`, `data-release` and `data-released`: rerun with `--apply` to write the `CHANGES:` lines into `index.html` (the weekly GitHub Action does this too). Only published GitHub releases count, not bare tags. The script already ignores bot commits and dependency bumps, and only ever raises `data-commits` (the page's older counts used a different method).
- A site marked `NEW: not linked from the page` that returned 200: add a link to its `<p class="links">`, before `Repo ↗`. Name it for what it is (`Try it ↗`, `Site ↗`, `Download ↗`, `Docs ↗`). `alecf.com/x` and `alecf.github.io/x` are the same site; link the `alecf.github.io` form like the other links do.

## 3. Read before rewriting copy

When the commits since the last update show real work (a new feature, a rewrite, a new site, a release), fetch the project's site or README and check the card still tells the truth: the description, the `stack` line, the links (e.g. a "Try it" link to the live app). Keep Alec's plain voice; change only what's now wrong or newly worth saying. Don't touch cards whose only news is dependency bumps.

## 4. Ask, don't add

For repos missing from the page, list them with their one-line descriptions and ask Alec which ones (if any) to add. Never add a project or change `data-status` on your own.

## 5. Check and report

Open `index.html` in a browser (or at least re-run the survey and confirm no `CHANGES:` lines remain), then tell Alec per project what changed and what you left for him.
