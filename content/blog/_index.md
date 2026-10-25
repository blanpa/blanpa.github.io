---
title: "Blog"
# The blog is hidden, not gone: every post and this index are drafts, so
# production builds (no --buildDrafts) leave /blog/ out of the site, the
# sitemap and the search index. docker-compose runs hugo server with
# --buildDrafts, so the posts are still there to read and edit locally.
# To publish again: drop draft: true here and in the posts, and restore the
# menu entry, mainSections and showRecent (see git log for the last time).
draft: true
description: "Technical articles on IIoT: Node-RED, industrial protocols (OPC-UA, Modbus, S7, EtherNet/IP), messaging, and edge computing."
showHero: true
heroStyle: "background"
cascade:
  showDate: true
  showAuthor: false
  showReadingTime: true
  showTableOfContents: true
  showHero: true
  # Was "background", the same mistake the projects section already fixed:
  # Blowfish washes the cover across the full width behind the title, and the
  # date, tag row and series bar land on top of the artwork. The covers are
  # drawn on paper, so behind light type on the dark theme they turned the
  # whole page header into a grey band. "basic" puts the plate above the
  # title, which is what a figure is for.
  heroStyle: "basic"
---
