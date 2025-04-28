import pytest
import json
import os
import lambda_function
import tempfile

# common constant objects
context = {}

# object 'event' is also common obj, but needs to be initialized each time


@pytest.fixture(scope='function', autouse=True)
def event_init():
    dir = os.path.dirname(__file__)
    f = open(dir + '/data/sample_event.json', 'r')
    event = json.load(f)
    yield event


def test_eventオブジェクトが読めること(event_init):
    assert event_init['path'] == '/receive'


def test_multipartがちゃんと読めること(event_init):
    email = lambda_function.parse_multipart_form(
        event_init['headers'],
        event_init['body']
    )
    assert 'from' in email
    assert 'to' in email
    assert 'subject' in email
    assert ('text' in email) or ('html' in email)

    # write out to html file
    html_text = lambda_function.create_html(email)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=True, mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(html_text)
        tmp_file.flush()

        # ファイルパスを取得
        file_path = tmp_file.name

        # ファイルパスを使用して、テストを実行
        assert os.path.exists(file_path)


def test_送信元アドレスがblacklistをパスすること(event_init):
    email = lambda_function.parse_multipart_form(
        event_init['headers'],
        event_init['body']
    )
    assert lambda_function.match_blacklist(email['from']) is False


def test_送信元アドレスがblacklistにヒットすること(event_init):
    spammer = 'Aleksandr <info@s6.ajgno.ru>'
    assert lambda_function.match_blacklist(spammer)


# def test_Lambda関数の全体処理が正常に完了すること(event_init):
#     _r = lambda_function.lambda_handler(event_init, context)
#     assert _r['statusCode'] == 201
