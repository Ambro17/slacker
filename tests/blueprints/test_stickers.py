from slacker.blueprints.stickers import _add_sticker
from slacker.models import Sticker


def test_sticker_unique_name(db, caplog):
    _add_sticker('U123', 'a name', 'a url')
    stickers = db.session.query(Sticker).all()
    assert len(stickers) == 1

    stdout = _add_sticker('U456', 'a name', 'another url')
    assert 'Something went wrong' in stdout
    assert 'UNIQUE constraint failed' in caplog.text
    stickers = db.session.query(Sticker).all()
    assert len(stickers) == 1


