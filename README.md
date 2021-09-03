# README

An AWS SAM application to keep your S3 buckets safe from viruses using ClamAV Open Source software
 
## Architecture Diagram

![Architecture Diagram!](/QuickStart-ClamAV.png "Quick Start ClamAV")

## Runtime Architecture 

1. New objects are uploaded to specific S3 buckets 
2. An EventBridge Rule triggers the lambda function 
3. Lambda function pulls the latest docker image from ECR registry
4. Lambda function scans the new object for viruses using ClamAV open source

## Development Flow

**A.** Developer pushes the code changes to the GitHub repo

**B.** GitHub WebHook triggers the CodeBuild build project

**C.** CodeBuild build project packages the application into the updated container image and uploads to ECR

**D.** CodeBuild build project updates the lambda function to use latest image

**E.** A Timer Event runs every 24 hours and triggers the build. Build process will update the container image with latest virus definitions, publishes to ECR and updates the lambda function

# Deployment Guide

## 1. Install the prerequisites
1. [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) and the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
2. [Configure the AWS CLI with your credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
3. AWS SAM requires Docker to be installed and running on developer machine. So [Install and run Docker on your local machine](https://www.docker.com/products/docker-desktop)
4. Create a new image repo using AWS console or CLI with the following command:

    `aws ecr create-repository --repository-name quickstart-clamav --image-tag-mutability IMMUTABLE --image-scanning-configuration scanOnPush=true`

    - Change the repo name if required. Default is **quickstart-clamav**

## 2. Initial Configuration

1. [Fork this repo](https://guides.github.com/activities/forking/) into your own GitHub account 
1. Run `git clone` to download the repo locally
1. [Create a personal access token from GitHub](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) 
   -  Under scopes, select **repo** - full control of private repositories and **admin:repo_hook** - full control of repository hooks
   -  Make sure to copy your personal access token value upon creation
   -  [Click here](https://docs.aws.amazon.com/codebuild/latest/userguide/access-tokens.html) for more information on using other source providers with CodeBuild
1. Store your token in [AWS SecretsManager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
   - Take note of the secret name and secret key
1. Push any pending code changes to your git repo using git commit and push commands.

## 3. SAM Setup and Deployment

1. Run `sam build` from the project home folder
   - [Click here for SAM build documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html)
1. Run `sam deploy -g --capabilities CAPABILITY_NAMED_IAM` and fill out the prompts
   - Input your `stack name`
   - Input the `AWS Region ID` that you want to run this solution
   - This solution deletes infected files by default. But if you want to tag files instead, select _Tag_ as the value for the `PreferredAction` parameter
   - Input ECR Repo URL of the image repo you created in the prerequisites for both `ECSREPO` and `image-repository` parameter 
     - Example: `ACCOUNT_ID`.dkr.ecr.`AWS_REGION`.amazonaws.com/`REPO_NAME`
   - Input your GITRepo URL as the value for `GITRepo` parameter
      - Example: https://github.com/`username`/`quickstart-clamav`.git
   - Input S3 bucket names for `S3Buckets` parameter as comma separated values
      - Example: bucket1,bucket2
   - Input `SecretName` and `SecretKey` you have noted from the previous step

## How to customize buckets or event triggers

1. Go to Amazon EventBridge in AWS console
1. Search for _virusscannerfn_ under Rules and click the rule to open
1. Update the event pattern and update the bucket names and/or event names
   - Learn more about [EventBridge rules here](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-log-s3-data-events.html#eb-log-s3-create-rule)
1. As a best practice, update the event pattern in template.yml accordingly and push the changes to your git repo

## Common Issues:
#### **Error -** CodeBuild fails to download updated antivirus definitions from the internet
- **Solution -** 
   - Add a VPC to your CodeBuild project by following these steps:
   - After the stack is deployed, [go to the CodeBuild Console](https://console.aws.amazon.com/codesuite/codebuild/projects) 
    - After the stack is deployed, [go to the CodeBuild Console](https://console.aws.amazon.com/codesuite/codebuild/projects) 
   - After the stack is deployed, [go to the CodeBuild Console](https://console.aws.amazon.com/codesuite/codebuild/projects) 
   - Once in the console, open the CodeBuild project [and add a VPC](https://docs.aws.amazon.com/codebuild/latest/userguide/vpc-support.html)
   - Click Validate VPC Settings to confirm there is internet connectivity
#### **Error -** Build fails with message like _Failed to call ImportSourceCredentials, reason: Token is required (Service: AWSCodeBuild; Status code: 400; Error Code: InvalidInputException; Request ID: xxx; Proxy: null)_
- **Solution -**
   - Ensure you have provided valid secret name and secret key for `SecretName` and `SecretKey`. You can lookup parameters in CloudFormation console -> Click on virusscanner stack -> Click on Parameters

## Limitations
1. This solution supports files up to 512MB size due to underlying lambda containers limit. Please consider these limits when deploying this solution. Read here for additional information: [Lambda function code can access a writable /tmp directory with 512 MB of storage](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#images-reqs). 
1. Currently, this solution must be deployed to a public AWS Region. GovCloud is not supported yet.
