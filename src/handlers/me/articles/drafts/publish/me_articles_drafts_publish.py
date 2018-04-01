# -*- coding: utf-8 -*-
import os
import json
import logging
import traceback
import settings
import time
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError, FormatChecker
from db_util import DBUtil


class MeArticlesDraftsPublish(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
            },
            'required': ['article_id']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft'
        )

    def exec_main_proc(self):
        self.__delete_article_content_edit()
        self.__create_article_history()

        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression='set #attr = :article_status',
            ExpressionAttributeNames={'#attr': 'status'},
            ExpressionAttributeValues={':article_status': 'public'}
        )

        return {
            'statusCode': 200
        }

    def __delete_article_content_edit(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])
        article_content_edit = article_content_edit_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        if article_content_edit:
            article_content_edit_table.delete_item(Key={'article_id': self.params['article_id']})

    def __create_article_history(self):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        article_content = article_content_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')

        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        article_history_table.put_item(
            Item={
                'article_id': article_content['article_id'],
                'title': article_content['title'],
                'body': article_content['body'],
                'created_at': int(time.time())
            }
        )