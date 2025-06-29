import boto3 
import json
import urllib.parse
import os
import re

s3 = boto3.client('s3')
bucket_name = 'file-converter-input-bucket'

# Allowed conversions map
allowed_conversions = {
    'docx': ['pdf', 'odt', 'txt', 'jpg', 'png'],
    'odt':  ['pdf', 'docx', 'txt', 'jpg', 'png'],
    'pptx': ['pdf', 'jpg', 'png'],
    'xlsx': ['pdf'],
    'txt':  ['pdf', 'docx', 'odt'],
    'pdf':  ['odt', 'txt', 'jpg', 'png'],
    'jpg':  ['pdf'],
    'png':  ['pdf']
}

def lambda_handler(event, context):
    query = event.get('queryStringParameters', {}) or {}

    filename = query.get('filename')
    target_format = query.get('format', 'pdf').lower()

    if not filename:
        return error_response("Missing filename parameter")

    # Extract source extension
    source_ext = os.path.splitext(filename)[-1][1:].lower()  # e.g., '.docx' → 'docx'

    if source_ext not in allowed_conversions:
        return error_response(f"Source format .{source_ext} is not supported")

    if target_format not in allowed_conversions[source_ext]:
        return error_response(f"Conversion from .{source_ext} to .{target_format} is not supported")

    # Clean & encode
    parsed_name = urllib.parse.quote_plus(filename)
    key = f"{parsed_name}.to_{target_format}"

    try:
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=300
        )

        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'uploadUrl': url,
                'key': key,
                'originalFilename': filename
            })
        }

    except Exception as e:
        return error_response(str(e))

def error_response(message):
    return {
        'statusCode': 400,
        'headers': cors_headers(),
        'body': json.dumps({'error': message})
    }

def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
