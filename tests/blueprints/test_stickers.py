from slacker.blueprints.stickers import _add_sticker
from slacker.models import Sticker


def test_sticker_unique_name(db, caplog):
    _add_sticker('U123', 'existing name', 'a url')
    stickers = db.session.query(Sticker).all()
    assert len(stickers) == 1

    stdout = _add_sticker('U456', 'existing name', 'different url')
    assert 'Something went wrong' in stdout
    assert 'UNIQUE constraint failed' in caplog.text
    stickers = db.session.query(Sticker).all()
    assert len(stickers) == 1


def test_add_sticker_missing_args(test_app):
    response = test_app.get('/sticker/add')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['text'] == 'Usage: `/add_sticker mymeme https://i.imgur.com/12345678.png`'


def test_add_sticker(db, test_app):
    response = test_app.post('/sticker/add',
                             data={'user_id': 2, 'text': 'mymeme https://mymemeurl.com'},
                             content_type='application/x-www-form-urlencoded')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['text'] == 'Sticker `mymeme` saved'


def test_send_sticker_missing_arg(test_app):
    response = test_app.post('/sticker/send',
                             data={},
                             content_type='application/x-www-form-urlencoded')

    assert response.json['text'] == "Bad usage. Usage: `/send_sticker sticker_name`"


def test_send_sticker_wrong_name(db, test_app):
    response = test_app.post('/sticker/send',
                             data={'text': 'sarasa'},
                             content_type='application/x-www-form-urlencoded')

    assert response.json['text'] == "No sticker found under `sarasa`"


def test_send_sticker(f, db, test_app):
    elfandewanda = 'U123'
    f.StickerFactory(author=elfandewanda, name='ricardo for', image_url='an_url')
    response = test_app.post('/sticker/send',
                             data={'user_id': elfandewanda, 'text': 'ricardo for'},
                             content_type='application/x-www-form-urlencoded')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == {
        'blocks': [
            {
                'alt_text': 'ricardo for',
                'image_url': 'an_url',
                'title': {'text': 'ricardo for', 'type': 'plain_text'},
                'type': 'image'
            },
            {
                'block_id': 'send_sticker_block_id',
                'elements': [
                    {
                        'action_id': 'send_sticker_action_id:ricardo for',
                        'style': 'primary',
                        'text': {'text': 'Send!', 'type': 'plain_text'},
                        'type': 'button',
                        'value': 'an_url'
                    }
                ],
                'type': 'actions'
            }
        ],
        'response_type': 'ephemeral'
    }


def test_list_sticker(db, f, test_app):
    f.StickerFactory(author='yo', name='mamaa', image_url='link')
    f.StickerFactory(author='el', name='miameee', image_url='otro_link')
    response = test_app.post('/sticker/list')
    assert response.json['text'] == '*Stickers*'
    assert response.json['response_type'] == 'ephemeral'
    assert response.json['blocks'] == [
        {
            'text': {
                'text': '*List of stickers*. You can send them with `/sticker <name>`',
                'type': 'mrkdwn'
            },
            'type': 'section'
        },
        {
            'accessory': {
                'alt_text': 'mamaa',
                'image_url': 'link',
                'type': 'image'
            },
            'text': {
                'text': 'mamaa',
                'type': 'plain_text'
            },
            'type': 'section'
        },
        {
            'accessory': {
                'alt_text': 'miameee',
                'image_url': 'otro_link',
                'type': 'image'
            },
            'text': {
                'text': 'miameee',
                'type': 'plain_text'
            },
            'type': 'section'
        }]


def test_list_stickers_no_stickers(db, test_app):
    response = test_app.post('/sticker/list')
    assert response.status_code == 200
    assert response.json['text'] == 'No stickers added yet.'


def test_delete_sticker_missing_name_arg(db, f, test_app):
    response = test_app.post('/sticker/delete')
    assert response.json['text'] == (
        'Bad Usage. /delete_sticker <name>.\n'
        'Note: Only the original uploader can delete the sticker'
    )


def test_delete_sticker_wrong_name(db, f, test_app):
    response = test_app.post('/sticker/delete', data={'text': 'wrong name', 'user_id': 'U123'})
    assert response.json['text'] == 'No sticker found under `wrong name`. Are you the original uploader?'


def test_delete_sticker(db, f, test_app):
    sticker = f.StickerFactory(author='U1', name='hello', image_url='url')
    response = test_app.post('/sticker/delete',
                             data={'text': sticker.name, 'user_id': sticker.author},
                             content_type='application/x-www-form-urlencoded')
    assert response.status_code == 200
    assert response.json['text'] == 'hello deleted :check:'
