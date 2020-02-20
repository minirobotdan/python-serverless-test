# python-serverless-test
Experimenting with Python + AWS Lambda, API Gateway &amp; geospacial queries in Athena.

## Brief
Write a program that accepts a decimal longitude and latitude location as input 
and displays the nearest airport, from the data file provided, as output. It is 
up to the candidate to decide how the input is captured and how the output is 
displayed.

## Environment
- Python 3.7 & venv
- Serverless (+ a plugin to bundle requirements.txt packages)
- boto3 (Python3 AWS library)
- AWS Lambda, LambdaEdge, API Gateway, Athena, Glue & S3.

## Result
API is accessible from a restful endpoint: 

[https://mwngfb24ql.execute-api.eu-west-1.amazonaws.com/dev/hello?lat=53.4808&lng=2.2426](https://mwngfb24ql.execute-api.eu-west-1.amazonaws.com/dev/hello?lat=53.4808&lng=2.2426)

It accepts the query string parameters "lat" & "lng" and returns a JSON response with the nearest matching result.

## Architecture & Rationale
I wanted to create an architecture where input data was automatically parsed and added to our API. This is quite useful when aggregating data from different sources.
The CSV file provided was added to an S3 bucket (our data lake, in this instance), and then crawled by an AWS Glue Crawler, which determines a schema and then creates tables within an Athena DB instance. 

Deployment of our query code was done via Serverless, which bundled dependencies and created a Lambda function from the handler method, and attached an API Gateway instance to managed HTTP requests.

```
Client (Browser, CURL, Postman, etc) --- HTTPS ---> API Gateway ---> Lambda ---> Athena ---> S3 data bucket
```

## Known issues, observations and TODOs
- Some string formatting issues with escape characters I need to resolve
- Query string parameter mapping in API Gateway config was done by hand, and did not make it into the cloudformation scripts.
- Some more verbose logging when capturing exceptions would make it more debuggable in the AWS Lambda interface.
- Athena/PrestoDB support for Geospatial queries is fairly comprehensive, but I think I prefer MongoDB's 2DSphere interface for this type of task.
- For some reason executing this query over Lambda is extremely slow (~5-20s) compared to the raw execution (~1-2s), even from a warm start. I need to look into why this might be, this happens using both the Python & NodeJS APIs.