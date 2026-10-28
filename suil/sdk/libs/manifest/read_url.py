from urllib.request import Request, urlopen

from suil.sdk.errors import ManifestError

TIMEOUT = 30
NO_CACHE = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}


def fetch_url(url: str) -> tuple[bytes, str | None]:
    """The body of `url` past any cache on the way, and its Last-Modified."""
    if not url.startswith(('http://', 'https://')):
        raise ManifestError(f'{url} is not an http(s) URL')

    try:
        with urlopen(Request(url, headers=NO_CACHE), timeout=TIMEOUT) as response:
            return response.read(), response.headers.get('Last-Modified')
    except OSError as error:
        raise ManifestError(f'cannot read {url}: {error}') from error


def read_url(url: str) -> bytes:
    return fetch_url(url)[0]
