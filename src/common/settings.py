parameters = {
    'limit': {
        'type': 'integer',
        'minimum': 1,
        'maximum': 100
    },
    'article_id': {
        'type': 'string',
        'minLength': 12,
        'maxLength': 12
    },
    'user_id': {
        'type': 'string',
        'minLength': 1,
        'maxLength': 255
    },
    'sort_key': {
        'type': 'integer',
        "minimum": 1,
        "maximum": 2147483647000000
    }
}

article_recent_default_limit = 20

users_articles_public_default_limit = 10
