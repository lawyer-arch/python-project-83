from bs4 import BeautifulSoup


def parse_html(html: str) -> tuple[str | None, str | None, str | None]:
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.find('h1')
    title = soup.find('title')
    description = soup.find('meta', attrs={'name': 'description'})

    h1_text = h1.text.strip() if h1 else None
    title_text = title.text.strip() if title else None
    description_text = description['content'].strip() if description else None

    return h1_text, title_text, description_text