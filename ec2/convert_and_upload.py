import sys 
import subprocess
import boto3
import os
import logging
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


session = boto3.session.Session(region_name="eu-north-1")
dynamodb = session.resource('dynamodb')
s3 = session.client('s3')
table = dynamodb.Table('FileConversionLogs')


input_bucket = 'file-converter-input-bucket'
output_bucket = 'file-converter-output-bucket'


s3_key = sys.argv[1]           
target_format = sys.argv[2]    


filename = os.path.basename(s3_key).split(".to_")[0]   
local_input = f"/tmp/{filename}"


logger.info(f" Downloading: {s3_key}")
s3.download_file(input_bucket, s3_key, local_input)


logger.info(f" Converting {filename} to {target_format}")
subprocess.run([
    "libreoffice", "--headless", "--convert-to", target_format, local_input, "--outdir", "/tmp"
], check=False)


converted_name = os.path.splitext(filename)[0] + f".{target_format}"  
local_output = f"/tmp/{converted_name}"


if not os.path.exists(local_output):
    logger.error(f" Converted file not found: {local_output}")
    raise FileNotFoundError(f"Converted file not found: {local_output}")


logger.info(f" Uploading {converted_name} to {output_bucket}")
s3.upload_file(local_output, output_bucket, converted_name)


try: # Change Key vvvv
    table.update_item(
        Key={'fileId': s3_key},  
        UpdateExpression="SET #s = :s, #t = :t, convertedFile = :cf",
        ExpressionAttributeNames={
            "#s": "status",
            "#t": "timestamp"
        },
        ExpressionAttributeValues={
            ":s": "converted",
            ":t": int(time.time()),
            ":cf": converted_name
        }
    )
    logger.info(f" DynamoDB updated for {s3_key}")

except Exception as e:
    logger.error(f" Failed to update DynamoDB for {s3_key}: {str(e)}")