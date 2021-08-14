# sendgrid-receiver-aws
A serverless email receiver with below components:
- SendGrid Incoming Webhook
- Amazon API Gatewawy
- AWS Lambda
- Amazon S3 bucket (email objects converted to html)
- Amazon CloudFront

## how to use
1. set up incoming webhook with
    - your email domain
    - generated API-Gateway endpoint

2. set up email viewer side
    - create S3 bucket
    - create CloudFront distribution with S3 bucket static web hosting

3. set up serverless components
    ```sh
    npm install -g serverless
    npm install
    pip install -r requirements.txt
    cp .env_sample .env
    vim .env
    SLS_PROF=<yourprofile> SLS_REGION=<regionname> SLS_STAGE=<stagename> npx sls deploy
    ```

## some more reference
see https://www.georgeorge.com/blog/article/tech/sendgrid-receiver-aws.html
