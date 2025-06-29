import boto3
import json
import os
import urllib.parse
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')


table_name = os.environ.get("DDB_TABLE_NAME", "FileConversionLogs")
bucket_name = os.environ.get("OUTPUT_BUCKET", "file-converter-output-bucket")
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        logger.info("Received event: %s", json.dumps(event))
        query = event.get('queryStringParameters') or {}
        key = query.get('key')

        if not key:
            logger.warning("Missing key")
            return response(400, {'error': 'Missing key'})

        logger.info(f"Tracking download for: {key}")

        
        matching = table.scan(
            FilterExpression='convertedFile = :cf',
            ExpressionAttributeValues={':cf': key}
        )

        if not matching['Items']:
            logger.warning(f"No matching log for {key}")
            return response(404, {'error': 'Not found in logs'})

        original_key = matching['Items'][0]['fileId'] # Change to your DynamoDB KEY i used fileId

        
        table.update_item(
            Key={'fileId': original_key}, # Change to your DynamoDB KEY i used fileId
            UpdateExpression='SET downloadCount = if_not_exists(downloadCount, :start) + :inc',
            ExpressionAttributeValues={':start': 0, ':inc': 1}
        )
        logger.info(f" Updated download count for {original_key}")

        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=300
        )
        logger.info(" Presigned URL generated")

        return response(200, {'url': url})

    except Exception as e:
        logger.exception("Unhandled exception in download function")
        return response(500, {'error': 'Internal Server Error'})

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
