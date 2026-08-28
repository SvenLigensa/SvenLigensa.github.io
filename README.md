<div align="center">

# Personal Website

[![Website](https://img.shields.io/badge/Website-Live-brightgreen?style=for-the-badge&logo=github)](https://svenligensa.github.io/)

Visit the live site: **[svenligensa.github.io](https://svenligensa.github.io/)**

</div>

---

## Development

Content is separate from the markup that renders it:

| Path | Holds |
| --- | --- |
| `_data/cv.yaml` | Profile, nav/section order, and the Education, Awards, Work and Teaching entries |
| `_data/papers/<slug>.md` | One paper or project — frontmatter for the metadata, body for the summary |
| `build.py` | The generator: templates, icons, and a small YAML/Markdown reader |

`index.html` is **generated** — edit the data files, not that file.

```sh
python3 build.py     # regenerate index.html
```

No dependencies, no venv.
Commit the regenerated `index.html` along with your content changes; GitHub Pages serves it from the repo root.

The empty `.nojekyll` file matters: without it GitHub Pages runs the repo through Jekyll, which skips directories starting with `_` — and the paper thumbnails under `_data/` would 404.

### Adding a paper

Drop a new `_data/papers/<slug>.md` in place. The filename becomes the modal's
id, and `date` (ISO `YYYY-MM-DD`) sorts it into the list, newest first.

For a thumbnail, put an image next to it under the same name —
`_data/papers/<slug>.png` (`.jpg`, `.webp`, `.gif` and `.svg` also work). It is
picked up automatically and shown at the top of the popup. To point somewhere
else, set `thumbnail:` in the frontmatter to a path relative to the repo root,
and `thumbnailAlt:` if the title does not describe the image well.

### Notes on the data format

`build.py` reads a deliberate subset of YAML: nested mappings, block lists,
inline lists `[a, b]`, and quoted scalars. Two rules keep it working:

- **Quote any value containing `: `**
- **Comments go on their own line**, never after a value.

Paper bodies are Markdown, limited to paragraphs with inline links, `**bold**`
and `*italic*`.
