import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError


LAMBDA_DIR = (
    Path(__file__).resolve().parents[1]
    / "lambda"
    / "process_callbacks"
)
sys.path.insert(0, str(LAMBDA_DIR))


@pytest.fixture
def processor():
    with patch.dict(
        "os.environ",
        {
            "TABLE_NAME": "callback-concierge-requests",
            "CONNECT_INSTANCE_ID": "test-instance",
            "CONNECT_CONTACT_FLOW_ID": "test-flow",
            "CONNECT_REGION": "eu-west-2",
        },
    ):
        with patch("boto3.resource") as mock_resource, patch(
            "boto3.client"
        ) as mock_client:
            mock_table = MagicMock()
            mock_resource.return_value.Table.return_value = mock_table

            mock_connect = MagicMock()
            mock_client.return_value = mock_connect

            sys.modules.pop("handler", None)
            handler = importlib.import_module("handler")

            handler.table = mock_table
            handler.connect = mock_connect

            yield handler, mock_table, mock_connect

            sys.modules.pop("handler", None)


def sample_callback():
    return {
        "callbackId": "cb_test123",
        "phoneNumber": "+27720000000",
        "reason": "Technical support",
        "status": "PENDING",
        "createdAt": "2026-10-12T09:00:00+00:00",
        "attempts": 0,
    }


def test_processes_pending_callback(processor):
    handler, table, connect = processor
    table.query.return_value = {"Items": [sample_callback()]}
    connect.start_task_contact.return_value = {
        "ContactId": "contact-123"
    }

    result = handler.lambda_handler({}, None)

    assert result == {"processed": 1, "skipped": 0, "failed": 0}
    connect.start_task_contact.assert_called_once()
    assert (
        connect.start_task_contact.call_args.kwargs["InstanceId"]
        == "test-instance"
    )
    assert (
        connect.start_task_contact.call_args.kwargs["ClientToken"]
        == "cb_test123"
    )
    assert table.update_item.call_count == 2


def test_skips_callback_already_claimed(processor):
    handler, table, connect = processor
    table.query.return_value = {"Items": [sample_callback()]}
    table.update_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "Already claimed",
            }
        },
        "UpdateItem",
    )

    result = handler.lambda_handler({}, None)

    assert result == {"processed": 0, "skipped": 1, "failed": 0}
    connect.start_task_contact.assert_not_called()


def test_records_failure_when_connect_call_fails(processor):
    handler, table, connect = processor
    table.query.return_value = {"Items": [sample_callback()]}
    connect.start_task_contact.side_effect = RuntimeError(
        "Simulated Connect failure"
    )

    result = handler.lambda_handler({}, None)

    assert result == {"processed": 0, "skipped": 0, "failed": 1}
    assert table.update_item.call_count == 2

    failure_update = table.update_item.call_args.kwargs
    assert ":failed" in failure_update["ExpressionAttributeValues"]
    assert (
        failure_update["ExpressionAttributeValues"][":failed"]
        == "FAILED"
    )