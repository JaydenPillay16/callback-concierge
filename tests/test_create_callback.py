import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


# Add the Lambda directory to Python's import path.
LAMBDA_DIR = Path(__file__).resolve().parents[1] / "lambda" / "create_callback"
sys.path.insert(0, str(LAMBDA_DIR))

import handler as create_callback_handler


def test_create_callback_success():
    event = {
        "body": json.dumps(
            {
                "phoneNumber": "+27821234567",
                "reason": "Billing enquiry",
            }
        )
    }

    mock_table = MagicMock()

    with patch.object(
        create_callback_handler,
        "TABLE_NAME",
        "callback-concierge-requests",
    ):
        with patch.object(
            create_callback_handler.dynamodb,
            "Table",
            return_value=mock_table,
        ):
            result = create_callback_handler.lambda_handler(event, None)

    assert result["statusCode"] == 201

    body = json.loads(result["body"])

    assert "callbackId" in body
    assert body["status"] == "PENDING"

    mock_table.put_item.assert_called_once()


def test_missing_phone_number():
    event = {
        "body": json.dumps(
            {
                "reason": "Billing enquiry",
            }
        )
    }

    result = create_callback_handler.lambda_handler(event, None)

    assert result["statusCode"] == 400

    body = json.loads(result["body"])

    assert body["message"] == "phoneNumber is required"


def test_missing_reason():
    event = {
        "body": json.dumps(
            {
                "phoneNumber": "+27821234567",
            }
        )
    }

    result = create_callback_handler.lambda_handler(event, None)

    assert result["statusCode"] == 400

    body = json.loads(result["body"])

    assert body["message"] == "reason is required"