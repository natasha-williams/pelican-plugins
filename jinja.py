
import os

from pelican import signals
from pelican.generators import PagesGenerator
from pelican.utils import is_selected_for_writing


class JinjaGenerator(PagesGenerator):
    def get_context(self, page):
        context = self.context.copy()
        context['page'] = page
        context.update(page._context)
        return context

    def generate_context(self):
        # TODO: Caching is set up and works, but if a theme template is updated
        # the page doesn't automatically update as it's based on file mtime
        for page in self.context['pages']:
            path = os.path.join(self.output_path, page.relative_source_path)

            if not is_selected_for_writing(self.settings, path):
                continue

            content = self.get_cached_data(page.relative_source_path, None)

            if content is None:
                jinja = self.env.from_string(page._content)
                content = jinja.render(self.get_context(page))

                self.cache_data(page.relative_source_path, content)

            page._content = content

        self.save_cache()
        self.readers.save_cache()

    def generate_output(self, writer):
        pass


def get_generators(sender):
    return JinjaGenerator


def register():
    signals.get_generators.connect(get_generators)
