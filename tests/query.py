#!/usr/bin/env python3
"""
usage: query.py [-h] [-u URL] query

positional arguments:
  query              api endpoint to query

optional arguments:
  -h, --help         show this help message and exit
  -u URL, --url URL  base url of web framework

example usage:
    query.py '/get/users'
    query.py '/get/users' --url 'http://localhost:8080'
"""
from rich import print
import argparse
import requests
import sys


def g(base_url, path):
    base_url = base_url.strip('/')
    url = f'{base_url}{path}'
    print(f"\n`{path}`")
    print("\nRequest:")
    print("```ruby")
    print(path)
    print("```")
    print("")

    r = requests.get(url)
    res = r.json() if r.status_code == 200 else r.text
    print("Response")
    print("```json")
    print(res)
    print("```")
    # return res

def main():
    examples = '''example usage:
    ./%(prog)s '/get/users'
    ./%(prog)s '/get/users' --url 'http://localhost:8080'
    '''

    ap = argparse.ArgumentParser(epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('query', help="api endpoint to query")
    ap.add_argument('-u', '--url', default="https://m2band.hopto.org", help='base url of web framework')
    args = ap.parse_args()

    g(base_url=args.url, path=args.query)

if __name__ == '__main__':
    sys.exit(main())
