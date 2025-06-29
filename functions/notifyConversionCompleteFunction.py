import boto3
import json
import urllib.parse
from datetime import datetime

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

# Config
table = dynamodb.Table('FileConversionLogs')
sns_topic_arn = 'arn:aws:sns:eu-north-1:YOUR_ACCOUNT_ID:FileConvertedTopic'

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

        # Look up original request in DynamoDB
        response = table.scan(
            FilterExpression='convertedFile = :cf',
            ExpressionAttributeValues={':cf': key}
        )

        if not response['Items']:
            print("No matching record found for", key)
            return {'statusCode': 404, 'body': 'Not found in logs'}

        item = response['Items'][0]

        # Generate a new download link
        s3 = boto3.client('s3')
        download_link = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=3600
        )

        # Update DynamoDB status
        table.update_item(
            Key={'fileId': item['fileId']}, # Change to your dynamodb
            UpdateExpression="SET #s = :s, downloadUrl = :url, completedAt = :ts",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'converted',
                ':url': download_link,
                ':ts': datetime.utcnow().isoformat()
            }
        )

        # Send email
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject='Your file has been converted!',
            Message=f"Your file has been converted successfully!\nDownload it here:\n{download_link}"
        )

        return {'statusCode': 200, 'body': 'Notification sent'}

    except Exception as e:
        print("Error:", str(e))
        return {'statusCode': 500, 'body': 'Error'}
