from unittest import TestCase
from users_articles_public import UsersArticlesPublic
from unittest.mock import patch, MagicMock
import yaml
import os
import boto3
import json


class TestUsersArticlesPublic(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        os.environ['ARTICLE_INFO_TABLE_NAME'] = 'ArticleInfo'

        f = open("./database.yaml", "r+")
        template = yaml.load(f)
        f.close()

        create_params = {'TableName': 'ArticleInfo'}
        create_params.update(template['Resources']['ArticleInfo']['Properties'])
        cls.dynamodb.create_table(**create_params)

        table = cls.dynamodb.Table('ArticleInfo')
        items = [
            {
                'article_id': 'draftId00001',
                'user_id': 'test_user_1',
                'status': 'draft',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000001',
                'user_id': 'test_user_1',
                'status': 'public',
                'sort_key': 1520150272000001
            },
            {
                'article_id': 'testid000002',
                'user_id': 'test_user_1',
                'status': 'public',
                'sort_key': 1520150272000002
            },
            {
                'article_id': 'testid000003',
                'user_id': 'test_user_2',
                'status': 'public',
                'sort_key': 1520150272000003
            },
            {
                'article_id': 'testid000004',
                'user_id': 'test_user_1',
                'status': 'public',
                'sort_key': 1520150272000004
            }
        ]

        for item in items:
            table.put_item(Item=item)

    @classmethod
    def tearDownClass(cls):
        table = cls.dynamodb.Table('ArticleInfo')
        table.delete()

    def assert_bad_request(self, params):
        function = UsersArticlesPublic(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        params = {
            'pathParameters': {
                'user_id': 'test_user_1'
            },
            'queryStringParameters': {
                'limit': '2'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000004',
                'user_id': 'test_user_1',
                'status': 'public',
                'sort_key': 1520150272000004
            },
            {
                'article_id': 'testid000002',
                'user_id': 'test_user_1',
                'status': 'public',
                'sort_key': 1520150272000002
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_evaluated_key(self):
        params = {
            'pathParameters': {
                'user_id': 'test_user_1'
            },
            'queryStringParameters': {
                'limit': '3',
                'article_id': 'testid000002',
                'sort_key': '1520150272000002'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        expected_items = [
            {
                'article_id': 'testid000001',
                'user_id': 'test_user_1',
                'status': 'public',
                'sort_key': 1520150272000001
            }
        ]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], expected_items)

    def test_main_ok_with_evaluated_key_with_no_limit(self):
        table = self.dynamodb.Table('ArticleInfo')

        for i in range(11):
            table.put_item(Item={
                'user_id': 'test_user_1',
                'article_id': 'test_limit_number' + str(i),
                'status': 'public',
                'sort_key': 1520150273000000 + i
                }
            )

        params = {
            'pathParameters': {
                'user_id': 'test_user_1'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(json.loads(response['body'])['Items']), 10)

    def test_main_with_no_recource(self):
        params = {
            'pathParameters': {
                'user_id': 'test_user_3'
            },
            'queryStringParameters': {
                'limit': '3'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['Items'], [])

    @patch("users_articles_public.validate", MagicMock(side_effect=Exception()))
    def test_main_ng_with_internal_server_error(self):
        params = {
            'pathParameters': {
                'user_id': 'test_user_1'
            },
            'queryStringParameters': {
                'limit': '3'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 500)

    def test_validation_with_no_path_params(self):
        params = {
            'queryStringParameters': {
                'limit': '3'
            }
        }

        self.assert_bad_request(params)

    def test_validation_with_no_query_params(self):
        params = {
            'pathParameters': {
                'user_id': 'test_user_1'
            }
        }

        response = UsersArticlesPublic(params, {}, self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)

    def test_validation_user_id_required(self):
        params = {
            'pathParameters': {}
        }

        self.assert_bad_request(params)

    def test_validation_user_id_max(self):
        params = {
            'pathParameters': {
                'user_id': ''
            }
        }

        self.assert_bad_request(params)

    def test_validation_user_id_min(self):
        params = {
            'pathParameters': {
                'user_id': 'A' * 256
            }
        }

        self.assert_bad_request(params)
