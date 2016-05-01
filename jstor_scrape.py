#!/usr/bin/env python3


"""Download the JStor data files for a search term.
"""


import argparse
import os
from pprint import pprint, pformat
import re
import shutil
import sys
import urllib.parse

from bs4 import BeautifulSoup
import requests


HOME = 'http://dfr.jstor.org/'
DISCIPLINES = [
    'Sociology',
    'Political Science',
    'Economics',
    'Anthropology',
    'History',
    'Public Policy & Administration',
    'General Science',
    'Biological Sciences',
    'Business',
    'Mathematics',
    'Statistics',
    'Language & Literature',
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

    def find_links(self, target, lazy=True):
        """\
        Finds the links with text equalling `target` and returns the Page.

        """
        for a in self.soup.find_all('a'):
            content = ' '.join(a.stripped_strings)
            if target == content:
                page = Page(
                    urllib.parse.urljoin(self.url, a['href']),
                    tag=a,
                    verbose=self.verbose,
                )
                if not lazy:
                    page.get()
                yield page

    def find_link(self, target, lazy=True, top=False):
        """\
        Finds a link with text equalling `target` and returns the Page or None.

        """
        next_page = next(self.find_links(target, lazy=lazy), None)
        if self.verbose and top:
            filename = os.path.join(
                'dump',
                clean_filename(target) + '.csv',
            )
            next_page.export_csv(target, filename)
        return next_page

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

    def submit_term(self, term, lazy=True):
        """\
        This acts like setting the term on the page and returns the new Page.
        """
        qv0 = self.soup.find('input', {'name': 'qv0'})
        form = qv0.find_parent('form')

        select = self.soup.find('select', {'name': 'qf0'})
        for option in select.find_all('option'):
            if 'selected' in option.attrs:
                search_range = option['value']
                break
        else:
            search_range = 'text'

        params = {
            'qv0': term,
            'qf0': search_range,
            }

        for hidden in form.find_all('input', {'type': 'hidden'}):
            params[hidden['name']] = hidden['value']

        page = Page(
            urllib.parse.urljoin(self.url, form['action']),
            tag=form,
            params=params,
            verbose=self.verbose,
        )
        if not lazy:
            page.get()
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

    def export_csv(self, label, output_file):
        """This outputs the CSV data for a label."""
        url = self.find_export_link(label)
        print('download <{}>'.format(url))
        response = requests.get(url)
        assert response.status_code == 200
        print('writing {}'.format(output_file))
        with open(output_file, 'w') as fout:
            fout.write(response.text)


def clean_filename(text):
    """This replaces all non-alphanumeric letters with an underscore."""
    return re.sub(r'\W+', '_', text).lower()


def reset(dirname):
    """Remove and re-create the directory, if it exists."""
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.makedirs(dirname)


def parse_args(argv=None):
    """Parse the command-line arguements. """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', help='ALL THE OUTPUT!')
    parser.add_argument('-r', '--reset', dest='reset', action='store_true',
                        help='Reset the output director{y|ies}.')
    parser.add_argument('-o', '--output', dest='output', metavar='OUTPUT_DIR',
                        action='store',
                        help='The directory to store the output in.')
    parser.add_argument('term_files', metavar='TERM_FILE', nargs='+',
                        help='File(s) listing terms to search for.')

    return parser.parse_args(argv)


def main():
    """main"""
    args = parse_args()

    if args.reset:
        reset(args.output)
        if args.verbose:
            reset('dump')

    print('open language')
    root = Page(HOME, verbose=args.verbose)
    lang = root.find_link('Language', lazy=False, top=True)
    print('select english')
    eng = lang.find_link('English', lazy=False)

    print('open discipline')
    disc = eng.find_link('Discipline', lazy=False, top=True)
    disciplines = disc.find_options('Discipline')
    if args.verbose:
        print('DISCIPLINE LINKS')
        pprint(disciplines)

    terms = set()
    for term_file in args.term_files:
        with open(term_file) as tfin:
            terms |= set(line.strip() for line in tfin)
    terms = sorted(terms)

    for disc_name in DISCIPLINES:
        disc_page = disciplines[disc_name]
        disc_clean = clean_filename(disc_name)

        years_open = disc_page.find_link('Year of Publication', lazy=False,
                                         top=True)

        for term in terms:
            term_clean = clean_filename(term)

            print('search for term "{}"'.format(term))
            term_page = years_open.submit_term(term)
            filename = os.path.join(
                args.output, '%s-%s.csv' % (disc_clean, term_clean),
                )
            print(
                'select discipline "{}" and open year of '
                'publication'.format(disc_name)
                )
            term_page.export_csv('Year of Publication', filename)


if __name__ == '__main__':
    main()
