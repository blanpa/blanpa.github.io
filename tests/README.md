# Content tests

These test the *articles*, not the site build. Hugo is happy to publish a post
with a wrong port number, a JSON sample that doesn't parse, a diagram that
renders as an error box, or a bearing frequency that doesn't follow from the
geometry the same paragraph states. These tests are not.

They run **locally, not in CI** — before the commit, through a git hook.

## Setup (once)

```bash
git config core.hooksPath .githooks
tests/run.sh                          # creates .venv on first run
```

From then on every `git commit` runs the fast suite (~10 s) and refuses the
commit if something fails. `git commit --no-verify` skips it.

## Running them by hand

```bash
tests/run.sh            # fast suite — everything except diagrams
tests/run.sh diagrams   # render every mermaid diagram (~8 min)
tests/run.sh all        # both
```

`node` and `bash` are used to check JavaScript and shell samples; tests that
need a missing tool skip rather than fail.

## What is covered

| File | Checks |
|------|--------|
| `test_frontmatter.py` | Required keys, description length, duplicate `series_order`, one spelling per tag site-wide |
| `test_code_blocks.py` | Every fenced sample parses — JSON, YAML, TOML, Python, JavaScript, shell — and the fence language is one we recognise |
| `test_links_and_diagrams.py` | Internal links resolve against `content/`; every ` ```mermaid ` block parses |
| `test_domain_facts.py` | The technical claims: port numbers, Sparkplug message types, hex↔decimal conversions, arithmetic stated in prose, table totals, own npm package names, figures quoted in more than one post, and the documented output of the posts' own code samples |

## Diagram tests

`test_mermaid_diagram_parses` needs mermaid-cli and renders each diagram in a
headless browser — about 1.5 s per diagram, so ~8 minutes for the whole site:

```bash
npm install -g @mermaid-js/mermaid-cli
tests/run.sh diagrams
```

It is skipped automatically when `mmdc` is not on `PATH`. The pre-commit hook
does not run all of them: it renders only the diagrams in the posts you are
committing, which is a few seconds.

## When a test fails

The failure message names the file, the line, and what the correct value would
be. Two cases where the *test* is what needs changing, not the post:

- a port or fence language the site legitimately uses for the first time —
  add it to the allowlist in the test, which is there to be edited;
- a claim that moved or was rewritten — the tests that pin specific
  calculations say so ("update this test") instead of silently passing.

## Adding a check

Guard a class of error, not a sentence. `test_hex_to_decimal_claims` scans
every post for `0x… = …` and verifies the arithmetic; that keeps working as
posts are added. A test asserting one paragraph's exact wording does not.
