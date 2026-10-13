data "archive_file" "create_callback" {
  type        = "zip"
  source_file = "${path.module}/../lambda/create_callback/handler.py"
  output_path = "${path.module}/../lambda/create_callback/function.zip"
}

resource "aws_lambda_function" "create_callback" {
  function_name = "callback-concierge-create-callback"
  role          = aws_iam_role.create_callback_lambda.arn

  handler = "handler.lambda_handler"
  runtime = "python3.13"

  filename         = data.archive_file.create_callback.output_path
  source_code_hash = data.archive_file.create_callback.output_base64sha256

  timeout     = 10
  memory_size = 256

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.callback_requests.name
    }
  }
}

data "archive_file" "process_callbacks" {
  type        = "zip"
  source_file = "${path.module}/../lambda/process_callbacks/handler.py"
  output_path = "${path.module}/../lambda/process_callbacks/function.zip"
}

resource "aws_lambda_function" "process_callbacks" {
  function_name = "callback-concierge-process-callbacks"
  role          = aws_iam_role.process_callbacks_lambda.arn

  handler = "handler.lambda_handler"
  runtime = "python3.13"

  filename         = data.archive_file.process_callbacks.output_path
  source_code_hash = data.archive_file.process_callbacks.output_base64sha256

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      TABLE_NAME            = aws_dynamodb_table.callback_requests.name
      CONNECT_INSTANCE_ID   = "8e86842f-ba31-4267-af69-9ca7200d894b"
      CONNECT_CONTACT_FLOW_ID = "a574bffb-8578-413c-bee6-2c3eb32ee8a9"
      CONNECT_REGION        = "eu-west-2"
    }
  }
}