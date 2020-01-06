def test_index(test_app):
    response = test_app.get('/')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == {
        'error': "You must specify a command route.",
    }


def test_unsigned_request_fails(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == {
        'error': "'Missing required headers'",
        'text': 'Bad request'
    }
