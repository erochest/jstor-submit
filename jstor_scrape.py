#!/usr/bin/env python3


"""Download the JStor data files for a search term.
"""


import argparse
import sys
import urllib.parse

from bs4 import BeautifulSoup
import requests


HOME = 'http://dfr.jstor.org/'
LANGUAGE = ('cs', 'la:eng^1.0')

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


def download(url):
    """Downloads and parses a URL."""
    r = requests.get(url)
    assert r.status_code == 200
    return BeautifulSoup(r.text, 'html.parser')


def find_link(source_url, soup, target):
    """\
    This looks for a link containing `target` and returns the full URL for it.
    """
    for a in soup.find_all('a'):
        content = ' '.join(a.stripped_strings)
        if target in content:
            yield (urllib.parse.urljoin(source_url, a['href']), a)


def find_options(source_url, soup, section_title):
    """\
    This finds all of the options under the section and returns a dict from
    label to URL.
    """
    links = {}

    for (_, a_tag) in find_link(source_url, soup, section_title):
        for sibling in a_tag.next_siblings:
            if sibling.name == 'ul':
                for li in sibling.find_all('li'):
                    for a in li.find_all('a'):
                        links[a.string] = urllib.parse.urljoin(
                            source_url, a['href'],
                        )

    return links


def parse_args(argv=None):
    """Parse the command-line arguements. """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('term', metavar='SEARCH_TERM', nargs='+',
                        help='Terms to search for.')

    return parser.parse_args(argv)


def main():
    """main"""
    # args = parse_args()
    root = download(HOME)
    print('finding the URL for English')
    for (lang_url, _) in find_link(HOME, root, 'Language'):
        print('LANGUAGE = <{}>'.format(lang_url))
        lang = download(lang_url)
        for (eng_url, _) in find_link(lang_url, lang, 'English'):
            print('ENGLISH = <{}>'.format(eng_url))


if __name__ == '__main__':
    main()
