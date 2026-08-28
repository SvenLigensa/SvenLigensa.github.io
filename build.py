#!/usr/bin/env python3
"""Build index.html from the content in _data/.

    python3 build.py

Reads _data/cv.yaml (profile, sections, entries) and _data/papers/*.md (one
file per paper or project) and writes index.html. Standard library only.
"""

import datetime
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "_data"
OUTPUT = ROOT / "index.html"


# ─── Minimal YAML ─────────────────────────────────────────────────────────────
# Supports the subset used in _data/: nested mappings, block lists, inline
# lists [a, b], and quoted scalars. Comments must be on their own line, and any
# value containing ": " must be quoted.


class YamlError(Exception):
    pass


def _split_key(text):
    """Return (key, rest) for 'key: value' / 'key:', or None if not a mapping."""
    if text[:1] in ('"', "'"):
        return None
    for i, ch in enumerate(text):
        if ch == ":" and (i + 1 == len(text) or text[i + 1] == " "):
            return text[:i].strip(), text[i + 1 :].strip()
    return None


def _scalar(text):
    """Parse one scalar: quoted string, inline list, or bare string."""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [_scalar(p.strip()) for p in inner.split(",")] if inner else []
    return text


def parse_yaml(text):
    """Parse the supported YAML subset into dicts, lists and strings."""
    lines = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        is_item = stripped.startswith("- ")
        if is_item:
            stripped = stripped[2:].strip()
            indent += 2
        lines.append((indent, stripped, is_item, lineno))
    if not lines:
        return {}
    value, i = _parse(lines, 0, lines[0][0])
    if i != len(lines):
        raise YamlError(f"line {lines[i][3]}: unexpected indentation")
    return value


def _parse(lines, i, indent):
    return (_parse_list if lines[i][2] else _parse_map)(lines, i, indent)


def _parse_list(lines, i, indent):
    out = []
    while i < len(lines) and lines[i][0] == indent and lines[i][2]:
        if _split_key(lines[i][1]) is None:
            out.append(_scalar(lines[i][1]))
            i += 1
        else:
            value, i = _parse_map(lines, i, indent, first_is_item=True)
            out.append(value)
    return out, i


def _parse_map(lines, i, indent, first_is_item=False):
    out = {}
    first = True
    while i < len(lines) and lines[i][0] == indent:
        if lines[i][2] and not (first and first_is_item):
            break
        pair = _split_key(lines[i][1])
        if pair is None:
            raise YamlError(f"line {lines[i][3]}: expected 'key: value'")
        key, rest = pair
        i += 1
        if rest:
            out[key] = _scalar(rest)
        elif i < len(lines) and lines[i][0] > indent:
            out[key], i = _parse(lines, i, lines[i][0])
        else:
            out[key] = ""
        first = False
    return out, i


def split_frontmatter(text):
    """Split a '---' delimited frontmatter block from the body below it."""
    if not text.startswith("---"):
        raise YamlError("file does not start with '---'")
    _, frontmatter, body = text.split("---", 2)
    return parse_yaml(frontmatter), body.strip()


# ─── Minimal Markdown ─────────────────────────────────────────────────────────
# Paper bodies are prose: blank-line separated paragraphs, with inline links,
# bold and italic. Anything more would need a real parser.

_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def markdown(text):
    """Render prose Markdown to a list of <p> lines."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        joined = " ".join(l.strip() for l in block.splitlines() if l.strip())
        joined = esc(joined)
        joined = _LINK.sub(r'<a href="\2" target="_blank" rel="noopener">\1</a>', joined)
        joined = _BOLD.sub(r"<strong>\1</strong>", joined)
        joined = _ITALIC.sub(r"<em>\1</em>", joined)
        out.append(f"<p>{joined}</p>")
    return out


# ─── Helpers ──────────────────────────────────────────────────────────────────

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def esc(value):
    """Escape text content."""
    return html.escape(str(value), quote=False)


def att(value):
    """Escape an attribute value."""
    return html.escape(str(value), quote=True)


def month_year(date):
    """date(2026, 11, 1) -> 'Nov 2026'. Not locale-dependent, unlike strftime."""
    return f"{MONTHS[date.month - 1]} {date.year}"


def slugify(label):
    """'Project Seminar' -> 'project-seminar', for the pill--* modifier class."""
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", label.lower()))


def author_list(authors):
    """['A', 'B', 'C'] -> 'A, B, and C'."""
    if len(authors) == 1:
        return authors[0]
    return f"{', '.join(authors[:-1])}, and {authors[-1]}"


# ─── Icons ────────────────────────────────────────────────────────────────────
# Every inline SVG on the site. Sizes are baked in, as each appears at one size.

ICONS = {
    "external": '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M17 7H7M17 7v10"/></svg>',
    "github": '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>',
    "close": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    "chevron": '<svg class="mobile-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>',
    "moon": '<svg class="icon-moon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
    "sun": '<svg class="icon-sun" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "dock-github": '<svg width="15" height="15" viewBox="84 7399 20 20" fill="currentColor" aria-hidden="true"><path d="M94,7399 C99.523,7399 104,7403.59 104,7409.253 C104,7413.782 101.138,7417.624 97.167,7418.981 C96.66,7419.082 96.48,7418.762 96.48,7418.489 C96.48,7418.151 96.492,7417.047 96.492,7415.675 C96.492,7414.719 96.172,7414.095 95.813,7413.777 C98.04,7413.523 100.38,7412.656 100.38,7408.718 C100.38,7407.598 99.992,7406.684 99.35,7405.966 C99.454,7405.707 99.797,7404.664 99.252,7403.252 C99.252,7403.252 98.414,7402.977 96.505,7404.303 C95.706,7404.076 94.85,7403.962 94,7403.958 C93.15,7403.962 92.295,7404.076 91.497,7404.303 C89.586,7402.977 88.746,7403.252 88.746,7403.252 C88.203,7404.664 88.546,7405.707 88.649,7405.966 C88.01,7406.684 87.619,7407.598 87.619,7408.718 C87.619,7412.646 89.954,7413.526 92.175,7413.785 C91.889,7414.041 91.63,7414.493 91.54,7415.156 C90.97,7415.418 89.522,7415.871 88.63,7414.304 C88.63,7414.304 88.101,7413.319 87.097,7413.247 C87.097,7413.247 86.122,7413.234 87.029,7413.87 C87.029,7413.87 87.684,7414.185 88.139,7415.37 C88.139,7415.37 88.726,7417.2 91.508,7416.58 C91.513,7417.437 91.522,7418.245 91.522,7418.489 C91.522,7418.76 91.338,7419.077 90.839,7418.982 C86.865,7417.627 84,7413.783 84,7409.253 C84,7403.59 88.478,7399 94,7399"/></svg>',
    "linkedin": '<svg width="15" height="15" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M28.778 1.004h-25.56c-0.008-0-0.017-0-0.027-0-1.199 0-2.172 0.964-2.186 2.159v25.672c0.014 1.196 0.987 2.161 2.186 2.161 0.010 0 0.019-0 0.029-0h25.555c0.008 0 0.018 0 0.028 0 1.2 0 2.175-0.963 2.194-2.159l0-0.002v-25.67c-0.019-1.197-0.994-2.161-2.195-2.161-0.010 0-0.019 0-0.029 0h0.001zM9.9 26.562h-4.454v-14.311h4.454zM7.674 10.293c-1.425 0-2.579-1.155-2.579-2.579s1.155-2.579 2.579-2.579c1.424 0 2.579 1.154 2.579 2.578v0c0 0.001 0 0.002 0 0.004 0 1.423-1.154 2.577-2.577 2.577-0.001 0-0.002 0-0.003 0h0zM26.556 26.562h-4.441v-6.959c0-1.66-0.034-3.795-2.314-3.795-2.316 0-2.669 1.806-2.669 3.673v7.082h-4.441v-14.311h4.266v1.951h0.058c0.828-1.395 2.326-2.315 4.039-2.315 0.061 0 0.121 0.001 0.181 0.003l-0.009-0c4.5 0 5.332 2.962 5.332 6.817v7.855z"/></svg>',
    "scholar": '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 24a7 7 0 1 1 0-14 7 7 0 0 1 0 14zm0-24L0 9.5l4.838 3.94A8 8 0 0 1 12 9a8 8 0 0 1 7.162 4.44L24 9.5z"/></svg>',
    "orcid": '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.372 0 0 5.372 0 12s5.372 12 12 12 12-5.372 12-12S18.628 0 12 0zM7.369 4.378c.525 0 .947.431.947.947s-.422.947-.947.947a.95.95 0 0 1-.947-.947c0-.525.422-.947.947-.947zm-.722 3.038h1.444v10.041H6.647V7.416zm3.562 0h3.9c3.712 0 5.344 2.653 5.344 5.025 0 2.578-2.016 5.025-5.325 5.025h-3.919V7.416zm1.444 1.303v7.444h2.297c3.272 0 4.022-2.484 4.022-3.722 0-2.016-1.284-3.722-4.097-3.722h-2.222z"/></svg>',
    "email": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
}


def icon(name):
    if name not in ICONS:
        raise KeyError(f"unknown icon: {name!r}")
    return ICONS[name]


# ─── Loading ──────────────────────────────────────────────────────────────────


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")


def find_thumbnail(path, meta):
    """Resolve a paper's thumbnail to a site-root-relative path, or None.

    An explicit `thumbnail:` in the frontmatter wins; otherwise an image
    sitting next to the .md file under the same name is picked up.
    """
    if meta.get("thumbnail"):
        explicit = ROOT / meta["thumbnail"]
        if not explicit.is_file():
            sys.exit(f"{path}: thumbnail not found: {meta['thumbnail']}")
        return explicit.relative_to(ROOT).as_posix()
    for extension in IMAGE_EXTENSIONS:
        candidate = path.with_suffix(extension)
        if candidate.is_file():
            return candidate.relative_to(ROOT).as_posix()
    return None


def load_papers():
    """Load _data/papers/*.md into a list, newest first."""
    papers = []
    for path in sorted((DATA / "papers").glob("*.md")):
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except (YamlError, ValueError) as exc:
            sys.exit(f"{path}: {exc}")
        for required in ("title", "date", "subtitle"):
            if required not in meta:
                sys.exit(f"{path}: missing required key '{required}'")
        try:
            meta["date"] = datetime.date.fromisoformat(meta["date"])
        except ValueError:
            sys.exit(f"{path}: date must be ISO format (YYYY-MM-DD)")
        # The filename is the slug, so the modal id and the aria-labelledby
        # reference that points at it can never drift apart.
        meta["slug"] = path.stem
        meta["body"] = body
        meta["thumbnail"] = find_thumbnail(path, meta)
        papers.append(meta)
    return sorted(papers, key=lambda p: p["date"], reverse=True)


# ─── Rendering ────────────────────────────────────────────────────────────────


def render_links(links):
    """The link row on an entry card."""
    parts = [
        f'<a class="modal-btn" href="{att(l["url"])}" target="_blank" rel="noopener">'
        f'{icon(l.get("icon", "external"))}{esc(l["label"])}</a>'
        for l in links
    ]
    return f'<div class="entry-links">{"".join(parts)}</div>'


def render_entry(entry):
    """One CV entry. Everything past date and title is optional, which is why
    this renders Education, Awards, Work and Teaching alike."""
    date = entry["date"]
    date = "<br/>".join(esc(d) for d in date) if isinstance(date, list) else esc(date)
    grade = entry.get("grade")

    out = ['      <div class="entry">']
    out += ['        <div class="entry-meta">', f'          <span class="date">{date}</span>', "        </div>"]
    out += ['        <div class="entry-body">']
    heading = esc(entry["title"])
    if grade:
        heading += f' <span class="grade">{esc(grade)}</span>'
    out.append(f"          <h3>{heading}</h3>")
    if entry.get("institution"):
        out.append(f'          <p class="institution">{esc(entry["institution"])}</p>')
    if entry.get("description"):
        out.append(f'          <p>{esc(entry["description"])}</p>')
    if entry.get("bullets"):
        out.append("          <ul>")
        out += [f"            <li>{esc(b)}</li>" for b in entry["bullets"]]
        out.append("          </ul>")
    if entry.get("pills"):
        out.append('          <div class="pill-row">')
        out += [
            f'            <span class="pill pill--{slugify(p)}">{esc(p)}</span>'
            for p in entry["pills"]
        ]
        out.append("          </div>")
    if entry.get("links"):
        out.append(f"          {render_links(entry['links'])}")
    out.append("        </div>")
    for sub in entry.get("sub", []):
        out += [
            '        <div class="sub-entry-meta">',
            f'          <span class="date">{esc(sub["date"])}</span>',
            "        </div>",
            '        <div class="sub-entry-body">',
            f'          <span class="sub-entry-title">{esc(sub["title"])}</span>',
        ]
        if sub.get("institution"):
            out.append(f'          <p class="institution">{esc(sub["institution"])}</p>')
        out.append("        </div>")
    out.append("      </div>")
    return out


def render_paper_card(paper):
    """A paper/project entry: same shape, but clickable and wired to its modal."""
    return [
        f'      <div class="entry entry--clickable" data-modal="modal-{att(paper["slug"])}"'
        ' role="button" tabindex="0" aria-haspopup="dialog">',
        '        <div class="entry-meta">',
        f'          <span class="date">{esc(month_year(paper["date"]))}</span>',
        "        </div>",
        '        <div class="entry-body">',
        f'          <h3>{esc(paper["title"])}</h3>',
        f'          <p class="institution">{esc(paper["subtitle"])}</p>',
        "        </div>",
        "      </div>",
    ]


def render_modal(paper):
    """The detail dialog for one paper/project."""
    slug = att(paper["slug"])
    label = paper.get("modalLabel") or f'{paper["subtitle"]} · {month_year(paper["date"])}'
    out = [
        f'  <!-- Modal: {esc(paper["title"])} -->',
        f'  <div id="modal-{slug}" class="modal-overlay" aria-hidden="true">',
        f'    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-{slug}-title">',
        '      <div class="modal-header">',
        "        <div>",
        f'          <p class="modal-label">{esc(label)}</p>',
        f'          <h2 class="modal-title" id="modal-{slug}-title">{esc(paper["title"])}</h2>',
        "        </div>",
        '        <button class="modal-close" aria-label="Close">',
        f"          {icon('close')}",
        "        </button>",
        "      </div>",
        '      <div class="modal-body">',
    ]
    if paper["thumbnail"]:
        alt = paper.get("thumbnailAlt", paper["title"])
        out.append(
            f'        <img class="modal-thumb" src="{att(paper["thumbnail"])}"'
            f' alt="{att(alt)}" loading="lazy" />'
        )
    if paper.get("links"):
        out.append('        <div class="modal-actions">')
        out += [
            f'          <a href="{att(l["url"])}" class="modal-btn" target="_blank" rel="noopener">'
            f'{icon(l.get("icon", "external"))}{esc(l["label"])}</a>'
            for l in paper["links"]
        ]
        out.append("        </div>")
    out.append("        <h3>Summary</h3>")
    out += [f"        {line}" for line in markdown(paper["body"])]
    if paper.get("authors") or paper.get("facts"):
        out += ["        <h3>Further Information</h3>", '        <table class="modal-table">']
        if paper.get("authors"):
            out.append(
                f'          <tr><td>Authors</td><td>{esc(author_list(paper["authors"]))}</td></tr>'
            )
        for key, value in paper.get("facts", {}).items():
            out.append(f"          <tr><td>{esc(key)}</td><td>{esc(value)}</td></tr>")
        out.append("        </table>")
    out += ["      </div>", "    </div>", "  </div>"]
    return out


SHOW_MORE_LABEL = "Show more"
SHOW_LESS_LABEL = "Show less"


def render_blocks(blocks, section):
    """Lay out a section's entries, collapsing the tail behind a toggle when the
    section sets `collapseAfter`."""
    limit = section.get("collapseAfter")
    if limit:
        try:
            limit = int(limit)
        except ValueError:
            sys.exit(f"section '{section['id']}': collapseAfter must be a number")

    out = []
    if not limit or len(blocks) <= limit:
        for block in blocks:
            out += [""] + block
        return out

    for block in blocks[:limit]:
        out += [""] + block

    more_id = f"{section['id']}-more"
    out += ["", f'      <div class="entry-more" id="{att(more_id)}" hidden>']
    for block in blocks[limit:]:
        out += ["  " + line for line in block]
    out.append("      </div>")
    out += [
        "",
        '      <button class="show-more" type="button" aria-expanded="false"'
        f' aria-controls="{att(more_id)}"'
        f' data-more="{att(SHOW_MORE_LABEL)}" data-less="{att(SHOW_LESS_LABEL)}">',
        f'        <span class="show-more-label">{esc(SHOW_MORE_LABEL)}</span>',
        "      </button>",
    ]
    return out


def render_nav(sections, indent):
    pad = " " * indent
    return [
        f'{pad}<li><a href="#{att(s["id"])}">{esc(s["nav"])}</a></li>' for s in sections
    ]


def render_page(cv, papers):
    profile = cv["profile"]
    sections = cv["sections"]

    out = [
        "<!DOCTYPE html>",
        '<html lang="en" data-theme="dark">',
        "<head>",
        '  <meta charset="UTF-8" />',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        f'  <title>{esc(profile["name"])}</title>',
        '  <link rel="icon" href="favicon.svg" type="image/svg+xml" />',
        '  <link rel="stylesheet" href="styles.css" />',
        '  <link rel="preconnect" href="https://fonts.googleapis.com" />',
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />',
        '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />',
        "</head>",
        "<body>",
        "",
        "  <header>",
        "    <nav>",
        f'      <a class="nav-name" href="#">{esc(profile["name"])}</a>',
        "      <ul>",
        *render_nav(sections, 8),
        "      </ul>",
        "      <!-- Mobile: active section button (shown only on mobile) -->",
        '      <button class="mobile-section-btn" id="mobile-section-btn" aria-haspopup="true" aria-expanded="false">',
        f'        <span id="mobile-section-label">{esc(sections[0]["nav"])}</span>',
        f"        {icon('chevron')}",
        "      </button>",
        "      <!-- Mobile: nav dropdown -->",
        '      <div class="mobile-nav-dropdown" id="mobile-nav-dropdown" aria-hidden="true">',
        "        <ul>",
        *render_nav(sections, 10),
        "        </ul>",
        "      </div>",
        '      <button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">',
        f"        {icon('moon')}",
        f"        {icon('sun')}",
        "      </button>",
        "    </nav>",
        "  </header>",
        "",
        "  <main>",
        "",
        '    <section id="about" class="hero">',
        f'      <h1>{esc(profile["name"])}</h1>',
        # tagline and bio hold intentional inline HTML, so they are not escaped.
        f'      <p class="tagline">{profile["tagline"]}</p>',
        f'      <p class="bio">{profile["bio"]}</p>',
        "    </section>",
        "",
    ]

    for section in sections:
        out.append(f'    <section id="{att(section["id"])}">')
        out.append(f'      <h2>{esc(section["heading"])}</h2>')
        if section.get("source") == "papers":
            blocks = [render_paper_card(p) for p in papers]
        else:
            blocks = [render_entry(e) for e in section.get("entries", [])]
        out += render_blocks(blocks, section)
        out += ["", "    </section>", ""]

    out += [
        "  </main>",
        "",
        '  <div class="dock" role="navigation" aria-label="Social links">',
    ]
    for link in profile["dock"]:
        classes = "dock-item" + (f' {link["class"]}' if link.get("class") else "")
        target = "" if link["url"].startswith("mailto:") else ' target="_blank" rel="noopener"'
        out += [
            f'    <a class="{classes}" href="{att(link["url"])}"{target}>',
            f'      {icon(link["icon"])}',
            f'      <span>{esc(link["label"])}</span>',
            "    </a>",
        ]
    out.append("  </div>")

    for paper in papers:
        out.append("")
        out += render_modal(paper)

    out += ["", '  <script src="script.js"></script>', "</body>", "</html>", ""]
    return "\n".join(out)


def main():
    try:
        cv = parse_yaml((DATA / "cv.yaml").read_text(encoding="utf-8"))
    except YamlError as exc:
        sys.exit(f"{DATA / 'cv.yaml'}: {exc}")
    papers = load_papers()
    OUTPUT.write_text(render_page(cv, papers), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(papers)} papers, {len(cv['sections'])} sections)")


if __name__ == "__main__":
    main()
