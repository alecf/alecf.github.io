#!/usr/bin/env python3
"""Survey alecf's GitHub projects against the <article class="proj"> blocks in index.html.

Prints a markdown report: for each project on the page, what GitHub says now
(last push, commit count, homepage, Pages site, latest release, commits since the
page's data-updated) and what differs. Then lists recently pushed public repos
that aren't on the page yet.

Read-only unless --apply, which writes the CHANGES (data-updated, data-commits,
data-release, data-released) into index.html. It never touches copy or links.

Usage: python3 survey.py [path/to/index.html] [--apply] [--owner alecf] [--days 120]
Needs: gh (authenticated; GH_TOKEN works).
"""
import json, re, subprocess, sys, urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

args = sys.argv[1:]
apply = "--apply" in args
args = [a for a in args if a != "--apply"]
owner = "alecf"
days = 120
if "--owner" in args:
    i = args.index("--owner"); owner = args[i + 1]; del args[i:i + 2]
if "--days" in args:
    i = args.index("--days"); days = int(args[i + 1]); del args[i:i + 2]
index_path = args[0] if args else "index.html"


def gh(path, *extra):
    r = subprocess.run(["gh", "api", path, *extra], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.stdout


def is_bot(c):
    login = ((c.get("author") or {}).get("login") or "").lower()
    name = c["commit"]["author"]["name"].lower()
    return login.endswith("[bot]") or "dependabot" in name or "renovate" in name or name.endswith("[bot]")


# Hand-made dependency bumps and release-bot style commits don't count as updates.
DEPS = re.compile(r"^(build|chore|ci)?\(?(deps|deps-dev|release)\)?[:!]|^(bump|deps)\b|^chore\(main\): release", re.I)


def human_commits(repo):
    """All commits on the default branch not made by bots (dependabot, release bots, ...), newest first."""
    r = subprocess.run(["gh", "api", "--paginate", f"repos/{repo}/commits?per_page=100", "--jq", ".[] | @json"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    commits = [json.loads(line) for line in r.stdout.splitlines() if line.strip()]
    return [c for c in commits if not is_bot(c)]


def probe(url):
    """Return the final status code for a URL (follows redirects), or None."""
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "homepage-survey"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


class Articles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.projects, self.cur, self.in_links = [], None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and "proj" in (a.get("class") or "").split():
            self.cur = {"id": a.get("id"), "links": [], **{k[5:]: v for k, v in a.items() if k.startswith("data-")}}
        elif self.cur is not None and tag == "p" and a.get("class") == "links":
            self.in_links = True
        elif self.cur is not None and self.in_links and tag == "a":
            self.cur["links"].append(a.get("href"))

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_links = False
        elif tag == "article" and self.cur is not None:
            self.projects.append(self.cur); self.cur = None


parser = Articles()
parser.feed(open(index_path, encoding="utf-8").read())
on_page = {}
updates = {}  # project id -> {attribute: new value}

print(f"# Project survey ({date.today()})\n")
for p in parser.projects:
    repo = p.get("repo")
    print(f"## #{p['id']}  ({repo or 'no data-repo'})")
    print(f"- page: status={p.get('status')} updated={p.get('updated')} commits={p.get('commits')}")
    print(f"- page links: {', '.join(p['links']) or '(none)'}")
    if not repo:
        print(); continue
    on_page[repo.lower()] = p["id"]
    j = gh(f"repos/{repo}")
    if not isinstance(j, dict):
        print("- !! repo not reachable via gh\n"); continue
    pushed = (j.get("pushed_at") or "")[:10]
    mine = human_commits(repo) or []
    n = len(mine) or None
    work = [c for c in mine if not DEPS.match(c["commit"]["message"])]
    last_human = (work or mine)[0]["commit"]["author"]["date"][:10] if mine else None
    homepage = (j.get("homepage") or "").strip()
    print(f"- github: last real commit={last_human} (last push={pushed}) human commits={n} archived={j.get('archived')} description={j.get('description')!r}")

    candidates = []
    if homepage:
        candidates.append(("homepage field", homepage))
    if j.get("has_pages"):
        pages = gh(f"repos/{repo}/pages")
        url = pages.get("html_url") if isinstance(pages, dict) else None
        url = url or f"https://{owner}.github.io/{j['name']}/"
        candidates.append(("GitHub Pages", url))
    norm = lambda u: (u.rstrip("/").lower().replace("http://", "https://")
                      .replace("://www.alecf.com", f"://{owner}.github.io").replace("://alecf.com", f"://{owner}.github.io"))
    seen = set()
    page_links = {norm(u) for u in p["links"] if u}
    for label, url in candidates:
        if norm(url) in seen:
            continue
        seen.add(norm(url))
        status = probe(url)
        linked = any(norm(l) == norm(url) or norm(l).startswith(norm(url) + "/") for l in page_links)
        flag = "" if linked else "  <-- NEW: not linked from the page"
        print(f"- site ({label}): {url} -> HTTP {status}{flag}")

    rel = gh(f"repos/{repo}/releases/latest")
    tag, released = None, None
    if isinstance(rel, dict) and rel.get("tag_name"):
        tag, released = rel["tag_name"], (rel.get("published_at") or "")[:10]
        print(f"- latest release: {rel['tag_name']} ({(rel.get('published_at') or '')[:10]}) {rel.get('html_url')}")
    tags = gh(f"repos/{repo}/tags?per_page=1")
    if isinstance(tags, list) and tags and not (isinstance(rel, dict) and rel.get("tag_name")):
        print(f"- latest tag (no release): {tags[0]['name']}")

    since = p.get("updated")
    if since:
        commits = [c for c in mine if c["commit"]["author"]["date"][:10] >= since]
        if commits:
            print(f"- {len(commits)} human commits since page's updated date ({since}):")
            for c in commits[:20]:
                msg = c["commit"]["message"].splitlines()[0][:100]
                print(f"    - {c['commit']['author']['date'][:10]} {msg}")
    want = {}
    if last_human and last_human != p.get("updated"):
        want["updated"] = last_human
    if n and n > int(p.get("commits") or 0):
        want["commits"] = str(n)
    if tag and tag != p.get("release"):
        want["release"] = tag
    if released and released != p.get("released"):
        want["released"] = released
    if want:
        updates[p["id"]] = want
        print("- CHANGES: " + "; ".join(f"data-{k} {p.get(k)} -> {v}" for k, v in want.items()))
    print()

cutoff = (date.today() - timedelta(days=days)).isoformat()
repos = gh(f"users/{owner}/repos?per_page=100&sort=pushed") or []
extra = [r for r in repos if not r["fork"] and not r["archived"] and r["full_name"].lower() not in on_page
         and (r.get("pushed_at") or "")[:10] >= cutoff and r["name"] != f"{owner}.github.io"]
print(f"## Public repos pushed since {cutoff} that aren't on the page\n")
for r in extra:
    site = r.get("homepage") or (f"https://{owner}.github.io/{r['name']}/" if r.get("has_pages") else "")
    print(f"- {r['full_name']}  pushed={r['pushed_at'][:10]}  stars={r['stargazers_count']}  "
          f"{('site=' + site + '  ') if site else ''}{r.get('description') or ''}")

if apply and updates:
    html = open(index_path, encoding="utf-8").read()
    for pid, want in updates.items():
        m = re.search(r'<article class="proj" id="' + re.escape(pid) + r'"[^>]*>', html)
        if not m:
            sys.exit(f"--apply: no <article> opening tag for #{pid}")
        tag_html = m.group(0)
        for k, v in want.items():
            attr = re.compile(r'\sdata-' + k + r'="[^"]*"')
            new = f' data-{k}="{v}"'
            tag_html = attr.sub(new, tag_html) if attr.search(tag_html) else tag_html[:-1] + new + ">"
        html = html[:m.start()] + tag_html + html[m.end():]
    open(index_path, "w", encoding="utf-8").write(html)
    print(f"\nApplied changes to {len(updates)} project(s) in {index_path}.")
