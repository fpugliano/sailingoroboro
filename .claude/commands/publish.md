Publish edits to the Sailing Oroboro blog. Work through every step below in order.
Stop and report clearly if any step reveals a problem — do not proceed past a failure.

Optional argument: a short commit message hint, e.g. `/publish add Azores post`.
If no argument is given, derive the message from the diff.

---

## Step 1 — Diff review

Run `git diff content/` and `git diff --stat HEAD` (or `git status --short` if nothing is staged).

Report a concise human-readable summary:
- Which content/*.md files were added or modified
- For each file: post title (from frontmatter), kind of change (new post / text edit / hero change / image added / etc.)
- Any other tracked files that changed (build.py, posts/*.html, blog.html, etc.)

Do NOT show the full raw diff — summarise it.

---

## Step 2 — Sanity check

For each added or modified file in content/:

**Frontmatter validation** (read the file, parse the YAML block between the `---` delimiters):
- Required fields present: `slug`, `title`, `date`
- `date` is valid YYYY-MM-DD
- `slug` matches the filename stem (e.g. `slug: azores` → file is `content/azores.md`)
- `hero:` if present, looks like a relative image path (no leading slash, no `http`, has an image extension)

**Body validation**:
- If `raw_html: true` — body must be non-empty and start with an HTML tag
- If no `raw_html` (authored markdown) — every `![]()` image must have non-empty alt text; no absolute R2 URLs in image src (should be relative paths)

**Report issues**: List any problems found. If there are blocking errors (missing required field, invalid YAML, empty body), stop here and tell the user what to fix. Non-blocking warnings (e.g. short body, missing hero) can be reported but should not stop the workflow.

---

## Step 3 — Rebuild

Run: `/usr/bin/python3 build.py`

Capture stdout/stderr. Check for success:
- Exit code 0
- Output contains `✓ Built` 
- No line starting with `ERROR:` or `WARNING:` (except the normal boto3 deprecation warning, which is harmless)

If the build fails, show the relevant error lines and stop.

Report the summary line from the build output (the `✓ Built N HTML files` line).

---

## Step 4 — Verify generated output

For each content/*.md that was added or modified:
- Confirm the corresponding `posts/<slug>.html` exists
- Read the first 60 lines of the generated HTML and confirm:
  - The `<h1>` matches the post title from frontmatter
  - The `og:image` meta tag is present and non-empty
  - The `<article>` section is non-empty

If any of these checks fail, stop and report.

---

## Step 5 — Stage and commit

Stage only website source and output files. Use explicit paths — do NOT use `git add -A` or `git add .`:

**Always stage** (if modified):
- `content/` — all modified/added .md files
- `posts/<slug>.html` — the regenerated post HTML for each changed content file
- `blog.html`
- `index.html`
- `build.py` (only if it was modified)

**Never stage** (ignore even if git shows them):
- `*.gpx`, `*.zip`, `combine_gpx.py`, `main.dart.js`
- `media-export-*/`, `wayback-failed.txt`
- Any file not part of the website build

Write the commit message:
- First line: concise summary of what changed (use `$ARGUMENTS` as a hint if provided, otherwise derive from the diff)
- No body paragraph needed for routine publishes
- Final line: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

Show the user the staged files and the commit message before committing, then commit.

---

## Step 6 — Push

Run `git push` and report the result (branch → remote, commit hash).

After pushing, remind the user that GitHub Pages takes ~30–60 seconds to deploy, then the live URL for each changed post is:
`https://sailingoroboro.com/posts/<slug>.html`
