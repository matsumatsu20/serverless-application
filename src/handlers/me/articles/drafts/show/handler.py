# -*- coding: utf-8 -*-
import boto3
from me_articles_drafts_show import MeArticlesDraftsShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_drafts_show = MeArticlesDraftsShow(event, context, dynamodb)
    return me_articles_drafts_show.main()
