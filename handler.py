import json
import datetime
import boto3
import time
from retrying import retry
from lambda_types import LambdaDict, LambdaContext

client = boto3.client('athena')
RETRY_COUNT = 15

# Rudimentary check to ensure our input makes sense.
def validate_latlng(lat, lng):
    if float(lat) >= -90 and float(lat) <= 90 and float(lng) >= -180 and float(lng) <= 180:
        return True
    else:
        return False

# Walk the data structure for athena to get the Data key/values
def get_var_char_values(d):
    return [obj['VarCharValue'] for obj in d['Data']]

# Decode stringified response from athena
def decode_athena_response(result):
    header, *rows = result['ResultSet']['Rows']
    header = get_var_char_values(header)
    result = [dict(zip(header, get_var_char_values(row))) for row in rows]
    return json.dumps(result)


# Lambda function body. Runs query based on lat/lng input to determine closest neighbour, accounting for 
def endpoint(event: LambdaDict, context: LambdaContext) -> LambdaDict:

        query = ""
        statusCode = 500
        lat = event['queryStringParameters']['lat']
        lng = event['queryStringParameters']['lng']
        
        try:
            # Some basic input validation.
            isvalid_latlng = validate_latlng(lat, lng)
            if (lat == None or lng == None or isvalid_latlng == False):
                raise ValueError
            else:

                # Select nearest single row, where distance between the two LAT/LNG values (accounting for curvature of the earth) is smallest.
                query += "SELECT * FROM AIRPORTS ORDER BY ST_Distance("
                query += "ST_GEOMETRY_TO_TEXT(ST_BUFFER(ST_POINT({}, {}),.072284)),".format(str(lat), str(lng))
                query += "ST_GEOMETRY_TO_TEXT(ST_BUFFER(ST_POINT(LATITUDE, LONGITUDE),.072284))"
                query += ") ASC LIMIT 1;"

                print(query)

                execution = client.start_query_execution(
                    QueryString = query,
                    QueryExecutionContext = {
                        'Database': 'python-serverless-test'
                    },
                    ResultConfiguration = {
                        'OutputLocation': 's3://python-serverless-test/results/'
                    }
                )

                query_execution_id = execution['QueryExecutionId']

                # Get execution status and check if it's succeeded, failed or still going.
                for i in range(1, 1 + RETRY_COUNT):

                    # get query execution
                    query_status = client.get_query_execution(QueryExecutionId = query_execution_id)
                    query_execution_status = query_status['QueryExecution']['Status']['State']

                    if query_execution_status == 'SUCCEEDED':
                        break

                    if query_execution_status == 'FAILED':
                        raise Exception("Query failed:" + query_execution_status)

                    else:
                        print('Sleeping, {}'.format(query_execution_status))
                        time.sleep(i)
                else:
                    client.stop_query_execution(QueryExecutionId = query_execution_id)
                    raise Exception('Query timed out')

                results = client.get_query_results(QueryExecutionId = query_execution_id)

                statusCode = 200
                body = {
                    'message': 'Requested nearest airport at position ' + str(lat) + ', ' + str(lng),
                    'results': decode_athena_response(results)
                }

        # If we hit a value error we probably had trouble casting the user's input to a float, or was rejected at the top of the method.
        except ValueError:
            statusCode = 500
            body = {
                'message': 'Missing arguments, or latitude/longitude provided were invalid.'
            }

        # If we run out of time or the query fails
        except Exception:
            statusCode = 500
            body = {
                'message': 'There was a problem executing the query.'
            }

        response: LambdaDict = {
            "statusCode": statusCode,
            "body": json.dumps(body)
        }

        return response

