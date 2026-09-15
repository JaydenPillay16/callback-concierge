resource "aws_apigatewayv2_api" "callback_api" {
  name          = "callback-concierge-api"
  protocol_type = "HTTP"
  description   = "Callback Concierge API"
}

resource "aws_apigatewayv2_integration" "create_callback" {
  api_id                 = aws_apigatewayv2_api.callback_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.create_callback.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_callback" {
  api_id    = aws_apigatewayv2_api.callback_api.id
  route_key = "POST /callbacks"
  target    = "integrations/${aws_apigatewayv2_integration.create_callback.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.callback_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_callback.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.callback_api.execution_arn}/*/*"
}