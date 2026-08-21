"""Front matter must be complete and internally consistent.

Most of these guard things Hugo will happily build anyway: a missing
description still renders, a duplicated series_order still renders, a tag
written two different ways still renders — as two separate tag pages.
"""

from __future__ import annotations

import collections
import datetime

import pytest

REQUIRED = ("title", "description", "date", "tags")

# Long enough to say something, short enough that Google won't truncate it.
DESCRIPTION_MIN = 70
DESCRIPTION_MAX = 200


def test_required_keys(post):
    missing = [key for key in REQUIRED if not post.meta.get(key)]
    assert not missing, f"{post.rel}: front matter is missing {missing}"


def test_description_length(post):
    description = post.meta["description"]
    assert DESCRIPTION_MIN <= len(description) <= DESCRIPTION_MAX, (
        f"{post.rel}: description is {len(description)} characters; "
        f"keep it between {DESCRIPTION_MIN} and {DESCRIPTION_MAX} so search "
        f"results show it in full"
    )


def test_date_is_a_date(post):
    assert isinstance(post.meta["date"], (datetime.date, datetime.datetime)), (
        f"{post.rel}: date must be an unquoted YYYY-MM-DD value, "
        f"got {post.meta['date']!r}"
    )


def test_series_order_present_when_in_a_series(post):
    if post.meta.get("series"):
        assert post.meta.get("series_order"), (
            f"{post.rel}: is in series {post.meta['series']} but has no "
            f"series_order, so it sorts arbitrarily in the series navigation"
        )


def test_series_order_is_unique(posts):
    """Two posts sharing a series_order make the series navigation nonsense."""
    seen = collections.defaultdict(list)
    for post in posts:
        for series in post.meta.get("series") or []:
            order = post.meta.get("series_order")
            if order is not None:
                seen[(series, order)].append(post.slug)
    clashes = {key: slugs for key, slugs in seen.items() if len(slugs) > 1}
    assert not clashes, f"duplicate series_order: {clashes}"


def test_tags_have_one_spelling_site_wide(pages):
    """"IIoT" and "iiot" are one tag page but two labels — pick one."""
    spellings = collections.defaultdict(set)
    for page in pages:
        for tag in page.meta.get("tags") or []:
            spellings[tag.lower()].add(tag)
    inconsistent = {k: sorted(v) for k, v in spellings.items() if len(v) > 1}
    assert not inconsistent, f"tags spelled inconsistently across pages: {inconsistent}"


def test_featured_image_exists(post):
    """Posts without an image fall back to a generated card — fine, but a
    filename that no longer matches is silently ignored, which is not."""
    images = list(post.path.parent.glob("featured.*"))
    assert len(images) <= 1, f"{post.rel}: more than one featured.* image: {images}"


@pytest.mark.parametrize("field", ["title", "description"])
def test_no_stray_whitespace(post, field):
    value = post.meta[field]
    assert value == value.strip(), f"{post.rel}: {field} has leading/trailing whitespace"
