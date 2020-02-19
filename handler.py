import json
import datetime
from lambda_types import LambdaDict, LambdaContext


def endpoint(event: LambdaDict, context: LambdaContext) -> LambdaDict:
    body = {
        'message': 'Hello, world!'
    }

    response: LambdaDict = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response