"""Local-demo static server and same-origin API proxy. No external services."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import urllib.request
import urllib.error

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='/app/dist', **kwargs)

    def proxy(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 <= size <= 2 * 1024 * 1024:
                self.send_error(413)
                return
            body = self.rfile.read(size) if self.command == 'POST' else None
            request = urllib.request.Request('http://backend:8000' + self.path, data=body,
                headers={'Content-Type': 'application/json', 'Host': 'localhost'}, method=self.command)
            try:
                response = urllib.request.urlopen(request, timeout=125)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                data = response.read()
                self.send_response(response.code)
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
        except (OSError, ValueError):
            self.send_error(502, 'Local API unavailable')

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy()
        else:
            if self.path.split('?')[0] in {'/', '/dashboard', '/dashboard/', '/dashboard/analytics', '/dashboard/analytics/', '/dashboard/catalog', '/dashboard/catalog/'}:
                self.path = '/index.html'
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy()
        else:
            self.send_error(405)

ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
