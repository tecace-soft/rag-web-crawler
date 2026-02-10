import hashlib


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def has_changed(old: list[dict] | None, new: list[dict]) -> bool:
    """
    Compare two snapshots (lists of page results). Returns True if any URL's
    content changed or if the set of URLs changed.
    """
    if not old:
        return True
    if len(old) != len(new):
        return True

    old_by_url = {p["url"]: p.get("content", "") for p in old}
    new_by_url = {p["url"]: p.get("content", "") for p in new}
    if set(old_by_url) != set(new_by_url):
        return True
    for url in new_by_url:
        if fingerprint(old_by_url[url]) != fingerprint(new_by_url[url]):
            return True
    return False
