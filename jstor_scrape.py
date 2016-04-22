#!/usr/bin/env python3


"""Download the JStor data files for a search term.
"""


import argparse
import os
from pprint import pprint, pformat
import re
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

    def __init__(self, url, tag=None, verbose=False, **kwargs):
        self.url = url
        self.verbose = verbose
        self.tag = tag
        self.get_args = kwargs
        self._soup = None
        self.response = None

    @property
    def soup(self):
        if self._soup is None:
            self.get()
        return self._soup

    def get(self, **kwargs):
        """If soup is empty, gets the resource at the URL."""
        get_args = self.get_args.copy()
        get_args.update(kwargs)

        if self.verbose:
            print('GET <{}> {}'.format(self.url, pformat(get_args)))
        resp = requests.get(self.url, **get_args)
        self.response = resp
        if self.verbose:
            print('RESPONSE <{}>: {}'.format(resp.url, resp.status_code))
            if not os.path.isdir('dump'):
                os.mkdir('dump')

            i = 0
            dump_file = 'dump/%04d.html' % (i,)
            while os.path.isfile(dump_file):
                i += 1
                dump_file = 'dump/%04d.html' % (i,)

            print('DUMP ' + dump_file)
            with open(dump_file, 'w') as fout:
                fout.write(resp.text)
            print()

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
                    verbose=self.verbose,
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

        a_tag = self.find_link(section_title).tag
        for sibling in a_tag.next_siblings:
            if sibling.name == 'ul':
                for li in sibling.find_all('li'):
                    a_sibling = li.find('a')
                    links[a_sibling.string] = Page(
                        urllib.parse.urljoin(self.url, a_sibling['href']),
                        tag=a_sibling,
                        verbose=self.verbose,
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
            verbose=self.verbose,
        )
        return page

    def find_export_link(self, section_title, data_format='csv'):
        """\
        Assuming the section is already open, this returns the link to the data
        format for export.
        """
        data_link = (self.find_link(section_title)
                     .tag
                     .find_next_sibling('div')
                     .find('a', string=data_format))
        return urllib.parse.urljoin(self.url, data_link['href'])


def clean_filename(text):
    """This replaces all non-alphanumeric letters with an underscore."""
    return re.sub(r'\W+', '_', text).lower()


def parse_args(argv=None):
    """Parse the command-line arguements. """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', help='ALL THE OUTPUT!')
    parser.add_argument('terms', metavar='SEARCH_TERM', nargs='+',
                        help='Terms to search for.')

    return parser.parse_args(argv)


def main():
    """main"""
    args = parse_args()

    print('open language')
    root = Page(HOME, verbose=args.verbose)
    lang = root.find_link('Language')
    print('select english')
    eng = lang.find_link('English')

    print('open discipline')
    disc = eng.find_link('Discipline')
    disciplines = disc.find_options('Discipline')
    if args.verbose:
        print('DISCIPLINE LINKS')
        pprint(disciplines)

    for (disc_name, disc_page) in disciplines.items():
        disc_clean = clean_filename(disc_name)

        print('select discipline "{}"'.format(disc_name))
        disc_selected = disc_page.find_link(disc_name)

        print('open year of publication')
        years_open = disc_selected.find_link('Year of Publication')

        for term in args.terms:
            term_clean = clean_filename(term)

            print('search for term "{}"'.format(term))
            term_page = years_open.submit_term(term)
            url = term_page.find_export_link('Year of Publication')

            print('download')
            response = requests.get(url)
            assert response.status_code == 200
            filename = '%s-%s.csv' % (disc_clean, term_clean)
            print('writing {}'.format(filename))
            with open(filename, 'w') as fout:
                fout.write(response.text)


if __name__ == '__main__':
    main()
