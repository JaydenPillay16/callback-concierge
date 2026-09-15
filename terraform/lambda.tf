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