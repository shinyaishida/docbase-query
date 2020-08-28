import sys
import os
import requests
import argparse
import json


def get_query_result(query):
    query_token = os.environ.get('DOCBASE_QUERY_TOKEN')
    domain = os.environ.get('DOCBASE_DOMAIN')
    query = '%20'.join(query)
    headers = { 'X-DocBaseToken': f'{query_token}' }
    query_uri = f'https://api.docbase.io/teams/{domain}/posts?q={query}'
    response = requests.get(query_uri, headers=headers)
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
formatters['plain'] = format_in_plain
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
        'choices': ['plain', 'json', 'slack'],
        'default': 'plain',
        'help': 'output format (plain by default)'
    }
}

def create_arg_parser():
    parser = argparse.ArgumentParser(**ARG_PARSER_CONF)
    for option, option_params in OPTIONS.items():
        parser.add_argument(option, **option_params)
    return parser

if __name__ == '__main__':
    arg_parser = create_arg_parser()
    args = vars(arg_parser.parse_args(sys.argv[1:]))
    posts = get_query_result(args['query'])
    result = f'{generate_hit_count_message(len(posts))}\n'
    formatter = formatters[args['f']]
    result += formatter(posts)
    print(result)
