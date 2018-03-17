# -*- coding: utf-8 -*-
import os
import boto3
import json
import logging
import decimal
import traceback
import settings
from boto3.dynamodb.conditions import Key, Attr
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder
from parameter_util import ParameterUtil


class UsersArticlesPublic(object):
    def __init__(self, event, context, dynamodb):
        self.event = event
        self.context = context
        self.dynamodb = dynamodb

    def main(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        schema = {
            'type': 'object',
            'properties': {
                'user_id': settings.parameters['user_id'],
                'limit': settings.parameters['limit'],
                'article_id': settings.parameters['article_id'],
                'sort_key': settings.parameters['sort_key']
            },
            'required': ['user_id']
        }


        try:
            params = self.event.get('pathParameters')

            if params is None:
                raise ValidationError('pathParameters is required')

            if self.event.get('queryStringParameters') is not None:
                params.update(self.event.get('queryStringParameters'))

            ParameterUtil.cast_parameter_to_int(params, schema)

            validate(params, schema)

            article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])

            limit = int(params.get('limit')) if params.get('limit') is not None else settings.users_articles_public_default_limit

            query_params = {
                'Limit': limit,
                'IndexName': 'user_id-sort_key-index',
                'KeyConditionExpression': Key('user_id').eq(params['user_id']),
                'FilterExpression': Attr('status').eq('public'),
                'ScanIndexForward': False
            }

            if params.get('article_id') and params.get('sort_key'):
                LastEvaluatedKey = {
                    'user_id': params['user_id'],
                    'article_id': params.get('article_id'),
                    'sort_key': int(params.get('sort_key'))
                }

                query_params.update({'ExclusiveStartKey': LastEvaluatedKey})

            responce = article_info_table.query(**query_params)

            return {
                'statusCode': 200,
                'body': json.dumps(responce, cls=DecimalEncoder)
            }
        except ValidationError as err:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Invalid parameter: {0}".format(err)})
            }

        except Exception as err:
            logger.fatal(err)
            traceback.print_exc()

            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }
