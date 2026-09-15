import json
import os
import uuid
from datetime import datetime, timezone

import boto3


TABLE_NAME = os.environ.get("TABLE_NAME")

dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    try:
        body = event.get("body", "{}")

        if isinstance(body, str):
            body = json.loads(body)

        phone_number = body.get("phoneNumber")
        reason = body.get("reason")

        if not phone_number:
            return response(
                400,
                {"message": "phoneNumber is required"}
            )

        if not reason:
            return response(
                400,
                {"message": "reason is required"}
            )

        callback_id = f"cb_{uuid.uuid4().hex}"
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            "callbackId": callback_id,
            "phoneNumber": phone_number,
            "reason": reason,
            "status": "PENDING",
            "createdAt": timestamp,
            "updatedAt": timestamp,
            "attempts": 0
        }

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=item)

        return response(
            201,
            {
                "callbackId": callback_id,
                "status": "PENDING"
            }
        )

    except Exception as error:
        print(
            json.dumps(
                {
                    "level": "ERROR",
                    "message": "Failed to create callback",
                    "error": str(error)
                }
            )
        )

        return response(
            500,
            {"message": "Internal server error"}
        )


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }