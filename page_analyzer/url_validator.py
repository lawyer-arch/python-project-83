import validators

from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_valid_url(url):
    errors = {}

    if not validators.url(url):
        errors['url'] = 'Некорректный формат URL'
    if url == "":
        errors['url'] = 'URL не может быть пустым'
    if len(url) > 255:
        errors['url'] = 'Слишком длинный URL (должен быть короче 255 символов)'

    return errors