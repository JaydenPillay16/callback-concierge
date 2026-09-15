import json
from unittest.mock import MagicMock, patch

import lambda_create_callback


def test_create_callback_success():
    event = {
        "body": json.dumps(
            {
                "phoneNumber": "+27821234567",
                "reason": "Billing enquiry"
            }
        )
    }

    mock_table = MagicMock()

    with patch.object(
        lambda_create_callback,
        "TABLE_NAME",
        "callback-requests"
    ):
        with patch.object(
            lambda_create_callback.dynamodb,
            "Table",
            return_value=mock_table
        ):
            result = lambda_create_callback.lambda_handler(event, None)

    assert result["statusCode"] == 201

    body = json.loads(result["body"])

    assert "callbackId" in body
    assert body["status"] == "PENDING"

    mock_table.put_item.assert_called_once()


def test_missing_phone_number():
    event = {
        "body": json.dumps(
            {
                "reason": "Billing enquiry"
            }
        )
    }

    result = lambda_create_callback.lambda_handler(event, None)

    assert result["statusCode"] == 400

    body = json.loads(result["body"])

    assert body["message"] == "phoneNumber is required"


def test_missing_reason():
    event = {
        "body": json.dumps(
            {
                "phoneNumber": "+27821234567"
            }
        )
    }

    result = lambda_create_callback.lambda_handler(event, None)

    assert result["statusCode"] == 400

    body = json.loads(result["body"])

    assert body["message"] == "reason is required"