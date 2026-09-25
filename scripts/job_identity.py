"""Stable identity for ByteDance jobs, independent of CSV order or title."""
import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def job_id(url):
    parts = urlsplit(url.strip())
    match = re.search(r"/position/(\d+)(?:/|$)", parts.path)
    if match:
        return f"BD-{match.group(1)}"
    # For atypical links, ignore fragments and tracking parameters.
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query)
                           if not k.lower().startswith(('utm_', 'spm'))))
    canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                            parts.path.rstrip('/'), query, ''))
    return 'BD-URL-' + hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]
