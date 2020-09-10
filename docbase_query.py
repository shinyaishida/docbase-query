import os
import sys
import logging
import requests
import json
import argparse


PROGRAM = os.path.basename(__file__)
DEFAULT_FORMAT = 'plain'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

logger = logging.getLogger(PROGRAM)
logger.setLevel(LOG_LEVEL)

def query(query_keywords, format=DEFAULT_FORMAT):
    logger.info(f'query: {query_keywords}')
    posts = get_query_result(query_keywords)
    count = len(posts)
    logger.info(f'found {count} result(s)')
    result = f'{generate_hit_count_message(count)}\n'
    logger.debug(f'output format: {format}')
    formatter = formatters.get(format, formatters[DEFAULT_FORMAT])
    result += formatter(posts)
    return result


def get_query_result(query):
    query_token = os.environ.get('DOCBASE_QUERY_TOKEN')
    domain = os.environ.get('DOCBASE_DOMAIN')
    query = '%20'.join(query)
    headers = { 'X-DocBaseToken': f'{query_token}' }
    query_uri = f'https://api.docbase.io/teams/{domain}/posts?q={query}'
    logger.debug(f'query request: {query_uri}')
    response = requests.get(query_uri, headers=headers)
    logger.debug(f'query response: {response}')
    if response.status_code == 200:
        return response.json()['posts']
    else:
        return []

def generate_hit_count_message(count):
    if count <= 0:
        return 'no results'
    elif count == 1:
        return '1 result'
    else:
        return f'{count} results'

def format_in_plain(posts):
    return '\n'.join([f"{post['url']}\t{post['title']}" for post in posts])

def format_in_json(posts):
    titles= {}
    titles['posts'] = [{k:post[k] for k in ('title', 'url')} for post in posts]
    return json.dumps(titles, indent=2, ensure_ascii=False)

def format_in_slack(posts):
    return '\n'.join([f"<{post['url']}|{post['title']}>" for post in posts])

formatters = {}
formatters[DEFAULT_FORMAT] = format_in_plain
formatters['json'] = format_in_json
formatters['slack'] = format_in_slack

ARG_PARSER_CONF = {
    'prog': os.path.basename(__file__),
    'description': 'query DocBase memos',
    'prefix_chars': '/'
}

OPTIONS = {
    'query': {
        'metavar': 'QUERY',
        'nargs': '+',
        'help': 'query string'
    },
    '/f': {
        'choices': [DEFAULT_FORMAT, 'json', 'slack'],
        'default': DEFAULT_FORMAT,
        'help': f'output format ({DEFAULT_FORMAT} by default)'
    },
    '/d': {
        'action': 'store_true',
        'help': 'debug mode'
    }
}

def create_arg_parser():
    parser = argparse.ArgumentParser(**ARG_PARSER_CONF)
    for option, option_params in OPTIONS.items():
        parser.add_argument(option, **option_params)
    return parser


def main(args):
    if args['d']:
        logger.setLevel(logging.DEBUG)
    result = query(args['query'], format=args['f'])
    print(result)


if __name__ == '__main__':
    arg_parser = create_arg_parser()
    args = vars(arg_parser.parse_args(sys.argv[1:]))
    main(args)
