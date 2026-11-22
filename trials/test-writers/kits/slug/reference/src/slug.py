import re
import unicodedata


def make_slug(title: str, max_length: int = 60) -> str:
    ascii_text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z0-9]+", ascii_text.lower())
    if not words:
        raise ValueError("the title has no letters or digits")
    slug = ""
    for word in words:
        candidate = word if not slug else f"{slug}-{word}"
        if len(candidate) > max_length:
            break
        slug = candidate
    return slug or words[0][:max_length]
