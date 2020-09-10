import os
import re
import sys
import logging
import argparse
from slack import RTMClient
from slack.errors import SlackApiError
import docbase_query


PROGRAM = os.path.basename(__file__)
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN', '')
MY_USER_ID = os.environ.get('SLACK_USER_ID', '')
MY_BOT_ID = os.environ.get('SLACK_BOT_ID', '')
QUERY_COMMAND = re.compile(r'dq\W+')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
HTTPS_PROXY = os.environ.get('https_proxy', None)

logging.basicConfig(level='INFO')
logger = logging.getLogger(PROGRAM)
logger.setLevel(LOG_LEVEL)


def someone_sent_text(data):
    return 'text' in data and \
        data.get('user', 'not me') != MY_USER_ID and \
        data.get('bot_id', 'not me') != MY_BOT_ID


@RTMClient.run_on(event='message')
def respond_to_message(**payload):
    data = payload['data']
    web_client = payload['web_client']
    if someone_sent_text(data):
        logger.debug(f'received: {data}')
        text = data.get('text', '')
        logger.debug(f'received command {text}')
        if QUERY_COMMAND.match(text):
            query_keywords = QUERY_COMMAND.sub('', text).split()
            logger.debug(f'received query {query_keywords}')
            query_result = query_docbase(query_keywords)
            channel_id = data['channel']
            thread_ts = data['ts']
            user = data['user']
            try:
                response = web_client.chat_postMessage(
                    channel=channel_id,
                    text=query_result,
                    thread_ts=thread_ts
                )
            except SlackApiErrors as e:
                logger.error(e.response['error'])


def query_docbase(query_keywords):
    return docbase_query.query(query_keywords, format='slack')


ARG_PARSER_CONF = {
    'prog': PROGRAM,
    'description': 'DocBase bot'
}

OPTIONS = {
    '--debug': {
        'action': 'store_true',
        'help': 'debug mode'
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
    if args['debug']:
        logger.setLevel(logging.DEBUG)
    rtm_client = RTMClient(token=SLACK_API_TOKEN, proxy=HTTPS_PROXY)
    rtm_client.start()
