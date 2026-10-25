from urllib.error import HTTPError
from urllib.request import urlopen

from suil.sdk.errors import ManifestError

TIMEOUT = 30


def read_url(url: str, missing: bytes | None = None) -> bytes:
    if not url.startswith(('http://', 'https://')):
        raise ManifestError(f'{url} is not an http(s) URL')

    try:
        with urlopen(url, timeout=TIMEOUT) as response:
            return response.read()
    except HTTPError as error:
        if error.code == 404 and missing is not None:
            return missing

        raise ManifestError(f'cannot read {url}: {error}') from error
    except OSError as error:
        raise ManifestError(f'cannot read {url}: {error}') from error
