---
headless: true
---

# Publishing a case study

Nothing in this section is live: `_index.md` and `_template/` both carry
`draft: true`, so a production build skips them entirely — they are absent
from the HTML, the sitemap, `llms.txt` and the search index. `hugo server -D`
(what `docker compose up` runs) shows them so you can work on one.

## Steps

1. `cp -r content/case-studies/_template content/case-studies/<slug>`
2. Fill in the front matter and the five sections. The template's comments say
   what belongs where.
3. Drop a `featured.webp` into the folder if you have an image — the list card
   and the social card use it, and both work without one.
4. Remove `draft: true` from the study, and from `_index.md` once the first
   one is ready.
5. Add the section to the navigation:

   ```toml
   # config/_default/menus.toml
   [[main]]
     name = "Case Studies"
     pageRef = "case-studies"
     weight = 15
   ```

## The one rule

Every number in `results:` has to be one the customer measured or would
recognise. Leave an entry out rather than estimate it — the rest of this site
publishes figures that can be checked (npm downloads, package versions, test
counts), and one invented percentage undermines all of them.

Anonymised is fine and needs no approval: "a tier-one automotive supplier, 40
machines" carries the same weight as a name.

## What renders from front matter

| Field | Where it appears |
|---|---|
| `client`, `duration`, `role` | Fact row under the title |
| `brief` | Lead paragraph |
| `results[].value` / `.label` | Result band — hidden entirely while every value is empty |
| `sector` | Kicker on the list card |
| `stack` | Chips at the foot of the study |

The first filled `results` entry is also the headline number on the list card.
