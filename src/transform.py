"""
Turns the two Commons API responses into the fields the views show.

Input (polled in this order):
  IDX_0: imageinfo of the file in Template:Potd/<date>
  IDX_1: wikitext of Template:Potd/<date> (<lang>) and (en), in any order
Output: image URL and size, caption (plain text, chosen language or English),
artist, licence, date and language. Empty strings when Commons has no picture.
"""
import html
import re

MAX_CAPTION = 400
MAX_ARTIST = 120
# Templates whose last plain parameter is the text to show, e.g. {{w|Enduro}} or {{w|Enduro|enduro}}.
LINK_TEMPLATES = {"w", "wd", "wikt", "wp", "wikipedia", "taxon", "lang", "nowrap", "nobold", "noitalic"}
TITLE = re.compile(r"\((?P<lang>[a-z-]+)\)$")


def strip_template(match):
    parts = match.group(1).split("|")
    name = parts[0].strip().lower()
    plain = [p for p in parts[1:] if "=" not in p]
    if name in LINK_TEMPLATES and plain:
        return plain[-1]
    return ""


def wikitext_to_plain(text):
    # The caption is the 1= parameter of {{Potd description|1=...|2=en|...}}.
    m = re.search(r"\|\s*1\s*=(.*?)\|\s*2\s*=", text, re.S)
    text = m.group(1) if m else text
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # Innermost templates first, until none are left.
    for _ in range(10):
        text, n = re.subn(r"\{\{([^{}]*)\}\}", strip_template, text)
        if not n:
            break
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)  # [[target|label]] and [[target]]
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)  # [url label]
    text = re.sub(r"'{2,}", "", text)  # ''italic'' and '''bold'''
    return clean(text)


def clean(text):
    text = re.sub(r"<br\s*/?>", " ", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def cut(text, limit):
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def captions(response):
    found = {}
    for page in ((response or {}).get("query") or {}).get("pages", []):
        m = TITLE.search(page.get("title", ""))
        revs = page.get("revisions") or []
        if not m or not revs:
            continue
        content = revs[0].get("slots", {}).get("main", {}).get("content", "")
        found[m.group("lang")] = wikitext_to_plain(content)
    return found


def requested_lang(response):
    langs = [TITLE.search(p.get("title", "")) for p in ((response or {}).get("query") or {}).get("pages", [])]
    langs = [m.group("lang") for m in langs if m]
    return next((l for l in langs if l != "en"), "en")


def run(input):
    pages = ((input.get("IDX_0") or {}).get("query") or {}).get("pages", [])
    page = next((p for p in pages if p.get("imageinfo")), None)
    caps = captions(input.get("IDX_1"))
    lang = requested_lang(input.get("IDX_1"))
    date = next((re.search(r"Potd/(\d{4}-\d{2}-\d{2})", p.get("title", "")) for p in
                 ((input.get("IDX_1") or {}).get("query") or {}).get("pages", [])), None)

    empty = {"img_url": "", "img_w": 0, "img_h": 0, "caption": "", "artist": "", "license": "",
             "date": date.group(1) if date else "", "lang": lang}
    if not page:
        return empty

    info = page["imageinfo"][0]
    meta = info.get("extmetadata") or {}
    name = re.sub(r"^File:|\.[a-z0-9]+$", "", page.get("title", ""), flags=re.I)
    caption = caps.get(lang) or caps.get("en") or name
    caption_lang = lang if caps.get(lang) else "en"

    return {
        **empty,
        "img_url": info.get("thumburl") or info.get("url", ""),
        "img_w": info.get("thumbwidth") or info.get("width", 0),
        "img_h": info.get("thumbheight") or info.get("height", 0),
        "caption": cut(caption, MAX_CAPTION),
        "caption_lang": caption_lang,
        "artist": cut(clean((meta.get("Artist") or {}).get("value")), MAX_ARTIST) or "Unknown author",
        "license": clean((meta.get("LicenseShortName") or {}).get("value")) or "See Wikimedia Commons",
    }
