# alecf.github.io

Alec's homepage: side projects first, then a topographic map of his career.

Everything lives in `index.html` (no build step). Screenshots live in `projects/<project-id>/`.

## Adding a project

1. Copy one of the `<article class="proj">` blocks in `index.html` and paste it where you want it in the list (order on the page is the order in the file).
2. Give it a new `id`. That's its shareable link: `alecf.github.io/#your-id`.
3. Write whatever HTML you like inside it. A few things get picked up automatically:
   - the `<h3>` is the project's name on the map
   - the first plain `<p>` becomes its note on the map
   - links inside `<p class="links">` show up on the map too
4. Optional `data-*` attributes on the `<article>`:

   | attribute | what it does |
   |---|---|
   | `data-status` | `open` (Live), `rough` (Early), `building` (In progress), or `idea` (Idea) |
   | `data-started` | `YYYY-MM-DD`. Puts its peak on the map beside that stretch of the career. Peaks worked on in the last 30 days (`data-updated`) get a flag |
   | `data-updated` | `YYYY-MM-DD`. Refreshed live from GitHub when `data-repo` is set |
   | `data-commits` | sets how tall its peak is on the map |
   | `data-repo` | `owner/name` on GitHub |
   | `data-short` | a shorter name for the elevation profile |

5. Drop screenshots in `projects/<id>/` and reference them with `<figure>`. Two images side by side: `<figure class="shots">`. Pixel art: add `class="pixels"` to the `<img>`.

## Other content

Career stops, interests and footer links are near the top of the `<script>` in `index.html`.

## Custom domain

To serve this from a domain like `www.alecf.com`, add a `CNAME` file containing the domain and point the DNS at GitHub Pages. Project sites under `alecf.github.io/<repo>/` (thicket, dr-creep-in-zig) will move with it automatically.
