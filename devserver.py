
import argparse
import os

from BaseHTTPServer import HTTPServer
from pelican import signals
from pelican.server import ComplexHTTPRequestHandler

REQUIRED_DIRECTORIES = []


class CustomHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, pelican, output):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

        self.pelican = pelican
        self.output_directory = output
        run_pelican(self.pelican, self.output_directory)


class CustomHTTPHandler(ComplexHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.base_path = server.output_directory

        ComplexHTTPRequestHandler.__init__(self, request, client_address,
                                           server)

    def do_GET(self):
        path = self.path

        if path.endswith('/'):
            path += 'index.html'

        if path.endswith('.html'):
            run_pelican(self.server.pelican, self.server.output_directory,
                        page=path)

        ComplexHTTPRequestHandler.do_GET(self)


def run_pelican(pelican, output_directory, page=''):
    cmd = 'pelican {settings} --write-selected {path}{page}'.format(
        settings=pelican, path=output_directory, page=page)
    os.system(cmd)


def page_generator_init(generator):
    paths = []

    for item in generator.settings['WRITE_SELECTED']:
        output_path = generator.output_path + '/'
        path = item.replace(output_path, '')

        paths.append(path)

        # If any pages are required for the page to load, add them
        for name in REQUIRED_DIRECTORIES:
            if name not in path or name in paths:
                continue

            paths.append(name)

    generator.settings['PAGE_PATHS'] = paths


def static_generator_init(generator):
    theme_directory = os.path.join(os.path.dirname(generator.output_path),
                                   generator.theme)
    static_path = generator.settings['THEME_STATIC_PATHS'][0]
    static_directory = os.path.join(theme_directory, static_path)
    generator.settings['IGNORE_FILES'] += [static_path]

    if not os.path.isdir(generator.output_path):
        os.mkdir(generator.output_path)

    for item in os.listdir(static_directory):
        source_path = os.path.join(static_directory, item)
        output_path = os.path.join(generator.output_path, item)

        if not os.path.islink(output_path):
            os.symlink(source_path, output_path)


def register():
    signals.page_generator_init.connect(page_generator_init)
    signals.static_generator_init.connect(static_generator_init)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate HTML on page load.')
    parser.add_argument('--pelican', dest='pelican', required=True,
                        help='The pelican settings to run.')
    parser.add_argument('--output', dest='output', required=True,
                        help='The output directory for generated files.')
    args = parser.parse_args()
    address = ('', 8000)
    CustomHTTPServer.allow_reuse_address = True
    httpd = CustomHTTPServer(address, CustomHTTPHandler, args.pelican,
                             args.output)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()
