#!/usr/bin/env python3


"""Download the JStor data files for a search term.
"""


import argparse
import sys
import urllib.parse

from bs4 import BeautifulSoup
import requests


HOME = 'http://dfr.jstor.org/'
DISCIPLINES = [
    'Sociology',
    'Political Science ',
    'Economics',
    'Anthropology',
    'History',
    'Public Policy and Administration ',
    'General Science',
    'Biological Sciences ',
    'Business',
    'Mathematics',
    'Statistics',
    'Language and Literature ',
    'Philosophy',
]


class Page:
    """This represents a page, its soup, possibly where we got the tag."""

    def __init__(self, url, soup=None, tag=None, **kwargs):
        self.url = url
        self._soup = soup
        self.tag = tag
        self.get_args = kwargs
        self.response = None

    @property
    def soup(self):
        if self._soup is None:
            self.get()
        return self._soup

    def get(self, **kwargs):
        """If soup is empty, gets the resource at the URL."""
        get_args = self.get_args.copy() + kwargs
        resp = requests.get(self.url, **get_args)
        self.response = resp
        assert resp.status_code == 200
        self._soup = BeautifulSoup(resp.text, 'html.parser')
        return self._soup

    def find_links(self, target):
        """\
        Finds the links with text equalling `target` and returns the Page.

        """
        for a in self.soup.find_all('a'):
            content = ' '.join(a.stripped_strings)
            if target == content:
                yield Page(
                    urllib.parse.urljoin(self.url, a['href']),
                    tag=a,
                )

    def find_link(self, target):
        """\
        Finds a link with text equalling `target` and returns the Page or None.

        """
        return next(self.find_links(target), None)

    def find_options(self, section_title):
        """\
        This finds all of the options under the section that's already open on
        the page. It returns a dict mapping from label to Page.
        """
        links = {}

        (_, a_tag) = self.find_link(section_title)
        for sibling in a_tag.next_siblings:
            if sibling.name == 'ul':
                for li in sibling.find_all('li'):
                    a_sibling = li.find('a')
                    links[a_sibling.string] = Page(
                        urllib.parse.urljoin(self.url, a_sibling['href']),
                        tag=a_sibling,
                    )

        return links

    def find_year_range(self):
        """Get the range of years available on the page."""
        start = end = None

        for inp in self.soup.find_all('input'):
            if inp['name'] == 'sy':
                start = int(inp['orig'])
            elif inp['name'] == 'ey':
                end = int(inp['orig'])

        return range(start, end + 1)

    def submit_term(self, term):
        """\
        This acts like setting the term on the page and returns the new Page.
        """
        qv0 = self.soup.find('input', {'name': 'qv0'})
        form = qv0.find_parent('form')
        params = {'qv0': term}

        for hidden in form.find_all('input', {'type': 'hidden'}):
            params[hidden['name']] = hidden['value']

        page = Page(
            urllib.parse.urljoin(self.url, form['action']),
            tag=form,
            params=params,
        )
        return page


def parse_args(argv=None):
    """Parse the command-line arguements. """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('terms', metavar='SEARCH_TERM', nargs='+',
                        help='Terms to search for.')

    return parser.parse_args(argv)


def main():
    """main"""
    args = parse_args()

    root = Page(HOME)

    lang = root.find_link('Language')
    eng = lang.find_link('English')
    years_open = eng.find_link('Year of Publication')
    disc = years_open.find_link('Discipline')
    disciplines = disc.find_options('Discipline')

    for (disc_name, disc_page) in disciplines.items():
        print('DISCIPLINE ' + disc_name)
        for term in args.terms:
            term_page = disc_page.submit_term(term)
            year_range = term_page.find_year_range()
            for year in year_range:
                pass


if __name__ == '__main__':
    main()
