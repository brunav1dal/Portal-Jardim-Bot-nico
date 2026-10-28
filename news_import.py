"""Read public article previews without accessing private network addresses."""
from html.parser import HTMLParser
import http.client
import ipaddress
import re
import socket
import ssl
from urllib.parse import urljoin, urlsplit, urlunsplit


class ImportErrorMessage(ValueError):
    pass


def public_url(value):
    if not isinstance(value, str) or len(value) > 1800 or any(ord(char) < 32 for char in value):
        raise ImportErrorMessage('Informe um link público válido de até 1.800 caracteres.')
    try:
        parts = urlsplit(value.strip())
        if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
            raise ValueError()
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        if port not in {80, 443}:
            raise ValueError()
        host = parts.hostname.encode('idna').decode('ascii')
    except (ValueError, UnicodeError):
        raise ImportErrorMessage('Use um link público que comece com http:// ou https://.')
    if host.lower() == 'localhost' or host.lower().endswith(('.localhost', '.local', '.internal')):
        raise ImportErrorMessage('O link precisa ser de um site público de notícias.')
    try:
        literal = ipaddress.ip_address(host)
        if not literal.is_global:
            raise ImportErrorMessage('O link precisa ser de um site público de notícias.')
    except ValueError as error:
        if isinstance(error, ImportErrorMessage):
            raise
    authority = f'[{host}]' if ':' in host else host
    default = 443 if parts.scheme == 'https' else 80
    if port != default:
        authority += ':' + str(port)
    return urlunsplit((parts.scheme, authority, parts.path or '/', parts.query, ''))


def fetch_public_resource(value, max_bytes, allowed_types):
    """Validate each redirect and connect to the already-validated IP, retaining TLS SNI."""
    current = public_url(value)
    for _ in range(5):
        parts = urlsplit(current)
        host = parts.hostname
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        try:
            addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
                raise ImportErrorMessage('O site ou a imagem não têm um endereço público permitido.')
            # Pin the connection to a checked address; do not resolve the hostname a second time.
            address = addresses[0][4][0]
            connection = http.client.HTTPSConnection(host, port, timeout=10) if parts.scheme == 'https' else http.client.HTTPConnection(host, port, timeout=10)
            raw_socket = socket.create_connection((address, port), timeout=10)
            try:
                connection.sock = ssl.create_default_context().wrap_socket(raw_socket, server_hostname=host) if parts.scheme == 'https' else raw_socket
                connection.request('GET', urlunsplit(('', '', parts.path or '/', parts.query, '')),
                                   headers={'User-Agent': 'OrquideaSolar/1.0 (article preview)', 'Accept-Encoding': 'identity', 'Accept': ', '.join(allowed_types)})
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    location = response.getheader('Location')
                    if not location:
                        raise ImportErrorMessage('O redirecionamento do site não informou um destino.')
                    current = public_url(urljoin(current, location))
                    continue
                if response.status != 200:
                    raise ImportErrorMessage('O site não permitiu a leitura automática. Você pode preencher os campos e enviar uma foto manualmente.')
                content_type = response.headers.get_content_type()
                if content_type not in allowed_types:
                    raise ImportErrorMessage('O link não retornou uma página de notícia ou uma imagem compatível.')
                if response.headers.get('Content-Encoding', 'identity').lower() not in {'', 'identity'}:
                    raise ImportErrorMessage('O site não disponibilizou uma prévia compatível. Preencha os dados manualmente.')
                data = response.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise ImportErrorMessage('A página ou imagem é grande demais para importar. Envie a foto manualmente.')
                charset = response.headers.get_content_charset() or 'utf-8'
                return data, current, charset
            finally:
                connection.close()
                raw_socket.close()
        except ImportErrorMessage:
            raise
        except (OSError, http.client.HTTPException, ValueError):
            raise ImportErrorMessage('Não foi possível acessar o site agora. Confira o link ou preencha a notícia manualmente.')
    raise ImportErrorMessage('O site redirecionou muitas vezes. Use o link direto da matéria.')


class ArticleMetadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.title_parts = []
        self.in_title = False
        self.link_image = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('property', attrs.get('name', '')).lower()
            if key and attrs.get('content') and key not in self.meta:
                self.meta[key] = attrs['content']
        elif tag == 'title':
            self.in_title = True
        elif tag == 'link' and attrs.get('rel', '').lower() == 'image_src':
            self.link_image = attrs.get('href', '')

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)


def import_article(link):
    data, final_url, charset = fetch_public_resource(link, 1500000, {'text/html', 'application/xhtml+xml'})
    charset_match = re.search(br'charset\s*=\s*["\x27]?([a-zA-Z0-9_-]+)', data[:4096])
    if charset_match:
        charset = charset_match[1].decode('ascii')
    try:
        html = data.decode(charset, errors='replace')
    except LookupError:
        html = data.decode('utf-8', errors='replace')
    parser = ArticleMetadata()
    parser.feed(html)
    meta = parser.meta
    def clean(value, limit):
        return ' '.join(value.split())[:limit]
    title = clean(meta.get('og:title') or meta.get('twitter:title') or ' '.join(parser.title_parts), 160)
    if not title:
        raise ImportErrorMessage('O site não forneceu um título. Preencha os campos manualmente.')
    summary = clean(meta.get('og:description') or meta.get('twitter:description') or meta.get('description', ''), 280)
    image_url = meta.get('og:image:secure_url') or meta.get('og:image') or meta.get('twitter:image') or meta.get('twitter:image:src') or parser.link_image
    image = None
    warning = ''
    if image_url:
        try:
            image, _, _ = fetch_public_resource(urljoin(final_url, image_url), 5000000, {'image/jpeg', 'image/png', 'image/webp'})
        except ImportErrorMessage:
            warning = 'Título e resumo importados. Envie uma foto para completar a capa: o site não liberou a imagem.'
    else:
        warning = 'Título e resumo importados. O site não informou uma imagem de capa; envie uma foto.'
    return {'title': title, 'summary': summary,
            'source': clean(meta.get('og:site_name') or urlsplit(final_url).hostname, 120),
            'url': final_url, 'image_bytes': image, 'warning': warning}
