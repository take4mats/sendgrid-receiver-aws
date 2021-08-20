import os
import json
import boto3
import requests
import io
import re
from cgi import FieldStorage
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

BUCKET_NAME = os.environ.get("BUCKET_NAME")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
BASEPATH = os.environ.get("BASEPATH")

BLACKLIST = [
    r'^.*\.ru>$',
]


def lambda_handler(event, context):
    '''
    lambda_handler
    '''
    print('event object in JSON: ')
    print(json.dumps(event))

    email = parse_multipart_form(event['headers'], event['body'])

    if match_blacklist(email['from']) is True:
        return {
            'statusCode': 403,
            'body': json.dumps('Filtered as spam!')
        }

    html_text = create_html(email)
    s3_filepath = upload_to_s3(html_text)
    slack_notifier(email, s3_filepath)

    return {
        'statusCode': 201,
        'body': json.dumps('Success!')
    }


def match_blacklist(frmmail):
    flag = False

    for banned in BLACKLIST:
        pattern = re.compile(banned)
        if pattern.match(frmmail) is not None:
            flag = True

    return flag


def parse_multipart_form(headers, body):
    '''
    Content-Type: multipart/form-data のコンテンツをパースする
    '''
    fp = io.BytesIO(body.encode('utf-8'))
    environ = {'REQUEST_METHOD': 'POST'}
    headers = {
        'content-type': headers['Content-Type'],
        'content-length': len(body.encode('utf-8'))
    }

    fs = FieldStorage(fp=fp, environ=environ, headers=headers)

    email = {}
    for f in fs.list:
        # print(
        #     "---\nname: ", f.name,
        #     "\nfilename: ", f.filename,
        #     "\ntype: ", f.type,
        #     "\nvalue: ", f.value,
        #     "\n"
        # )
        email[f.name] = f.value

    return email


def create_html(email):
    '''
    構造化された email オブジェクトを使って、 閲覧用 HTML を生成する
    '''
    # specify jinja2 template file
    env = Environment(loader=FileSystemLoader('./', encoding='utf8'))
    template = env.get_template('template_email_html.j2')

    # render with given data
    html_text = template.render({'email': email})

    return html_text


def upload_to_s3(message):
    '''
    html に変換されたメッセージを S3 bucket に保存する
    '''
    s3 = boto3.client('s3')
    directory = (datetime.now() + timedelta(microseconds=0)).isoformat()

    filepath = '{dir}/index.html'.format(dir=directory)
    response = s3.put_object(
        Body=message,
        Bucket=BUCKET_NAME,
        Key=filepath,
        ContentType='text/html'
    )

    print('s3_upload uploaded to: {dir}'.format(dir=directory))
    print('s3_upload response in JSON: ')
    print(json.dumps(response))

    return filepath


def slack_notifier(email, s3_filepath):
    '''
    受信したメールのサマリを slack に通知する
    '''
    print('slack_notifier input: ')
    print(json.dumps(email))

    # message url uploaded to S3
    message_url = BASEPATH + '/' + s3_filepath

    # time the email has been sent
    _t1 = email['headers'].split('\n')
    _t2 = _t1[0].split(', ')
    time = _t2[1]

    # email body
    body = ''
    if 'text' in email:
        body = email['text']
    elif 'html' in email:
        body = '(Check the HTML message at {url} )'.format(url=message_url)

    # compose incoming webhook POST body
    request_body = {
        "text": "email to {to}: {url}".format(to=email['to'], url=message_url),
        "attachments": [
            {
                "title": "{subject}".format(subject=email['subject']),
                "fields": [
                    {
                        "title": "Time",
                        "value": time,
                        "short": True
                    },
                    {
                        "title": "From",
                        "value": email['from'],
                        "short": True
                    },
                    {
                        "title": "To",
                        "value": email['to'],
                        "short": True
                    },
                    {
                        "title": "Body",
                        "value": body,
                        "short": False
                    }
                ]
            }
        ]
    }

    # make POST request
    _r = requests.post(WEBHOOK_URL, data=json.dumps(request_body))

    print('slack_notifier response in JSON: ')
    response = {
        'status_code': _r.status_code,
        'headers': dict(_r.headers),
        'body': _r.text
    }
    print(json.dumps(response))

    return
