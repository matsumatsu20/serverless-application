# -*- coding: utf-8 -*-
import os
import settings
import time
from db_util import DBUtil
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil
from user_util import UserUtil


class MeArticlesPvCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        # single
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')
        validate(self.event.get('pathParameters'), self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.event['pathParameters']['article_id'],
            status='public'
        )

    def exec_main_proc(self):
        try:
            article_pv_user_table = self.dynamodb.Table(os.environ['ARTICLE_PV_USER_TABLE_NAME'])
            self.__create_article_pv_user(article_pv_user_table)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 200
                }
            else:
                raise

        return {
            'statusCode': 200
        }

    def __create_article_pv_user(self, article_pv_user_table):
        epoch = int(time.time())
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        article_user_id = self.__get_article_user_id(self.event['pathParameters']['article_id'])
        article_pv_user = {
            'article_id': self.event['pathParameters']['article_id'],
            'user_id': user_id,
            'article_user_id': article_user_id,
            'created_at': epoch,
            'target_date': time.strftime('%Y-%m-%d', time.gmtime(epoch)),
            'sort_key': TimeUtil.generate_sort_key()
        }

        # 追加のaliasの存在判定
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        article_user = users_table.get_item(Key={'user_id': article_user_id}).get('Item')
        user = users_table.get_item(Key={'user_id': user_id}).get('Item')
        if 'alias_user_id' in article_user:
            article_pv_user.update({'article_alias_user_id': article_user['alias_user_id']})
        if 'alias_user_id' in user:
            article_pv_user.update({'alias_user_id': user['alias_user_id']})

        article_pv_user_table.put_item(
            Item=article_pv_user,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __get_article_user_id(self, article_id):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        return article_info_table.get_item(Key={'article_id': article_id}).get('Item').get('user_id')
