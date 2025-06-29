import boto3
import json
import os
import urllib.parse
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')

# Config
output_bucket = 'file-converter-output-bucket' #create this S3
input_bucket = 'file-converter-input-bucket' #create this S3
ec2_instance_id = 'YOUR_INSTANCE_ID'
sns_topic_arn = 'arn:aws:sns:eu-north-1:YOUR_ACCOUNT_ID:FileConvertedTopic'
dynamodb_table_name = 'FileConversionLogs' # dynamodb

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    if '.to_' not in key:
        return {'statusCode': 400, 'body': 'Invalid file key format'}

    original_filename = key.split('.to_')[0]  
    target_format = key.split('.to_')[1]      
    new_key = os.path.splitext(original_filename)[0] + f".{target_format}"

    table = dynamodb.Table(dynamodb_table_name)

    try:
        # trigger EC2 conversion
        ssm.send_command(
            InstanceIds=[ec2_instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [f'python3 /home/ubuntu/convert_and_upload.py "{key}" "{target_format}"']
            },
        )

        # Generate presigned download link for the expected output
        download_link = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': output_bucket, 'Key': new_key},
            ExpiresIn=3600
        )

        # Log to DynamoDB
        table.put_item(Item={
            'fileId': key, # I used fileId change to your dynamodb key
            'convertedFile': new_key,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'conversion_started',
            'downloadUrl': download_link
        })

        # notify user
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject='Your file is being converted!',
            Message=f'We’ve received your file ({original_filename}) and started converting it to {target_format.upper()}.\nYou’ll receive another email once it’s ready.'
        )

        return {
            'statusCode': 200,
            'body': json.dumps(f'Started conversion of {original_filename} to {target_format}')
        }

    except Exception as e:
        print("Error:", str(e))
        table.put_item(Item={
            'fileId': key, # I used fileId change to your dynamodb key
            'convertedFile': new_key,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'error',
            'errorMessage': str(e)
        })
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to start conversion')
        }
