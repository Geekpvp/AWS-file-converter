# AWS File Converter

A serverless document converter using AWS Lambda, S3, DynamoDB, EC2 + LibreOffice.

## Features
- Upload files via S3
- Convert DOCX, PPTX, etc. to PDF
- Email notifications via SNS
- Download tracking with DynamoDB

## Tech Stack
- AWS Lambda, S3, DynamoDB, SNS, EC2
- Python backend
- HTML frontend

## Frontend
- `index.html` to upload
- `logs.html` to view logs + download

## How to Deploy
1. Upload HTML to S3 static website
2. Deploy Lambda functions
3. Set up DynamoDB + EC2
4. Permissions:Don't forget to attach some of following IAM permissions:
        sns:Publish
        dynamodb:GetItem
        dynamodb:UpdateItem
        logs:CreateLogGroup, logs:PutLogEvents, logs:CreateLogStream
        ssm:SendCommand
        ssm:ListCommandInvocations
        iam:PassRole

## available conversions
    'docx': ['pdf', 'odt', 'txt', 'jpg', 'png'],
    'odt':  ['pdf', 'docx', 'txt', 'jpg', 'png'],
    'pptx': ['pdf', 'jpg', 'png'],
    'xlsx': ['pdf'],
    'txt':  ['pdf', 'docx', 'odt'],
    'pdf':  ['odt', 'txt', 'jpg', 'png'],
    'jpg':  ['pdf'],
    'png':  ['pdf'] 

## This was Built as a project for Uni.