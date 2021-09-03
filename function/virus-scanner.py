import boto3
import os
import sys
import subprocess
import uuid
from urllib.parse import unquote_plus

s3_client = boto3.client('s3')


def lambda_handler(event, context):
    bucket = None
    key = None

    try:
        bucket = event['detail']['requestParameters']['bucketName']
        key = event['detail']['requestParameters']['key']
        file_name = '/tmp/' + key.split('/')[-1]

        # Updating the object's scan status to in progress
        tag_response = s3_client.put_object_tagging(
            Bucket=bucket,
            Key=key,
            # versionId=version,
            Tagging={'TagSet': [
                {
                    'Key': 'ScanStatus',
                    'Value': 'InProgress'
                }
            ]})

        s3_client.download_file(bucket, key, file_name)

        scan_cmd = 'clamscan --quiet ' + file_name
        sp = subprocess.Popen(scan_cmd,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True)

        out, err = sp.communicate()

        # * clamscan return values (documented from man clamscan)
        # *  0 : No virus found.
        # *  1 : Virus(es) found.
        # * 40: Unknown option passed.
        # * 50: Database initialization error.
        # * 52: Not supported file type.
        # * 53: Can't open directory.
        # * 54: Can't open file. (ofm)
        # * 55: Error reading file. (ofm)
        # * 56: Can't stat input file / directory.
        # * 57: Can't get absolute path name of current working directory.
        # * 58: I/O error, please check your file system.
        # * 62: Can't initialize logger.
        # * 63: Can't create temporary files/directories (check permissions).
        # * 64: Can't write to temporary directory (please specify another one).
        # * 70: Can't allocate memory (calloc).
        # * 71: Can't allocate memory (malloc).

        return_code = sp.wait()

        if return_code == 0:
            print("Clean file found, updating the object with scan status tags...")
            # Update tags with scan status
            tag_response = s3_client.put_object_tagging(
                Bucket=bucket,
                Key=key,
                # versionId=version,
                Tagging={'TagSet': [
                    {
                        'Key': 'ScanStatus',
                        'Value': 'Completed'
                    },
                    {
                        'Key': 'Tainted',
                        'Value': 'No'
                    },
                ]})
        elif return_code == 1:
            preferredAction = os.environ.get('preferredAction')
            print("Infected file found. Performing '" +
                    preferredAction + "' action on the file...")

            if preferredAction == "Delete":
                delete_response = s3_client.delete_object(Bucket=bucket,
                                                            Key=key,
                                                            # VersionId=version
                                                            )
                print(
                    "Deleting the infected file. Response: " + str(delete_response))
            else:
                tag_response = s3_client.put_object_tagging(
                    Bucket=bucket,
                    Key=key,
                    # versionId=version,
                    Tagging={'TagSet': [
                        {
                            'Key': 'ScanStatus',
                            'Value': 'Completed'
                        },
                        {
                            'Key': 'Tainted',
                            'Value': 'Yes'
                        },
                    ]})

                print("Tagging the infected file. Response: " +
                        str(tag_response))
        else:
            print(
                f"Unknown error occured while scanning the {key} for viruses.")
            tag_response = s3_client.put_object_tagging(
                Bucket=bucket,
                Key=key,
                # versionId=version,
                Tagging={'TagSet': [
                    {
                        'Key': 'ScanStatus',
                        'Value': 'Error'
                    },
                    {
                        'Key': 'Tainted',
                        'Value': 'Unknown'
                    },
                ]})

    except:
        print(f"Unknown error occured while scanning the {key} for viruses.")
        tag_response = s3_client.put_object_tagging(
            Bucket=bucket,
            Key=key,
            # versionId=version,
            Tagging={'TagSet': [
                {
                    'Key': 'ScanStatus',
                    'Value': 'Error'
                },
                {
                    'Key': 'Tainted',
                    'Value': 'Unknown'
                },
            ]})
