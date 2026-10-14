import json
import logging
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]
CONNECT_INSTANCE_ID = os.environ["CONNECT_INSTANCE_ID"]
CONNECT_CONTACT_FLOW_ID = os.environ["CONNECT_CONTACT_FLOW_ID"]
CONNECT_REGION = os.environ.get("CONNECT_REGION", "eu-west-2")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

connect = boto3.client(
    "connect",
    region_name=CONNECT_REGION,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def lambda_handler(event, context):
    logger.info(
        json.dumps({
            "message": "Callback processor started",
            "request_id": getattr(context, "aws_request_id", None),
        })
    )

    processed = 0
    skipped = 0
    failed = 0
    
    eligible_only = os.environ.get("PROCESS_ELIGIBLE_ONLY", "true").lower() == "true"

    
    callbacks = []
    query_kwargs = {
        "IndexName": "StatusIndex",
        "KeyConditionExpression": Key("status").eq("PENDING"),
    }

    while True:
        response = table.query(**query_kwargs)
        callbacks.extend(response.get("Items", []))

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

        query_kwargs["ExclusiveStartKey"] = last_evaluated_key

    for callback in callbacks:
        
        if eligible_only and callback.get("processingEligible") is not True:
            skipped += 1
            logger.info(
                json.dumps({
                    "message": "Callback is not eligible for processing",
                    "callback_id": callback.get("callbackId"),
                })
            )
            continue

        callback_id = callback["callbackId"]

        try:
            # Claim the callback so concurrent runs cannot both process it.
            table.update_item(
                Key={"callbackId": callback_id},
                UpdateExpression=(
                    "SET #status = :processing, updatedAt = :updated "
                    "ADD attempts :one"
                ),
                ConditionExpression="#status = :pending",
                ExpressionAttributeNames={
                    "#status": "status",
                },
                ExpressionAttributeValues={
                    ":processing": "PROCESSING",
                    ":pending": "PENDING",
                    ":updated": utc_now(),
                    ":one": 1,
                },
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == (
                "ConditionalCheckFailedException"
            ):
                skipped += 1
                logger.info(
                    json.dumps({
                        "message": "Callback already claimed",
                        "callback_id": callback_id,
                    })
                )
                continue

            failed += 1
            logger.exception(
                "Failed to claim callback %s", callback_id
            )
            continue

        try:
            phone_number = callback["phoneNumber"]
            reason = callback["reason"]

            task = connect.start_task_contact(
                InstanceId=CONNECT_INSTANCE_ID,
                ContactFlowId=CONNECT_CONTACT_FLOW_ID,
                Name=f"Callback: {reason}"[:256],
                Description=(
                    f"Return call to {phone_number}. "
                    f"Reason: {reason}. "
                    f"Callback ID: {callback_id}"
                )[:4096],
                Attributes={
                    "callbackId": callback_id,
                    "phoneNumber": phone_number,
                    "reason": reason,
                },
                ClientToken=callback_id,
            )

            table.update_item(
                Key={"callbackId": callback_id},
                UpdateExpression=(
                    "SET #status = :created, updatedAt = :updated, "
                    "connectContactId = :contact_id"
                ),
                ConditionExpression="#status = :processing",
                ExpressionAttributeNames={
                    "#status": "status",
                },
                ExpressionAttributeValues={
                    ":created": "CONTACT_CREATED",
                    ":processing": "PROCESSING",
                    ":updated": utc_now(),
                    ":contact_id": task["ContactId"],
                },
            )

            processed += 1
            logger.info(
                json.dumps({
                    "message": "Connect task created",
                    "callback_id": callback_id,
                    "contact_id": task["ContactId"],
                })
            )

        except Exception:
            failed += 1
            logger.exception(
                "Failed to create task for callback %s", callback_id
            )

            # Keep the request visible for investigation. We do not
            # automatically retry here because Connect may have created
            # a task before an unexpected error occurred.
            try:
                table.update_item(
                    Key={"callbackId": callback_id},
                    UpdateExpression=(
                        "SET #status = :failed, updatedAt = :updated"
                    ),
                    ConditionExpression="#status = :processing",
                    ExpressionAttributeNames={
                        "#status": "status",
                    },
                    ExpressionAttributeValues={
                        ":failed": "FAILED",
                        ":processing": "PROCESSING",
                        ":updated": utc_now(),
                    },
                )
            except Exception:
                logger.exception(
                    "Could not record failure for callback %s",
                    callback_id,
                )

    result = {
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
    }

    logger.info(
        json.dumps({
            "message": "Callback processor finished",
            **result,
        })
    )

    return result