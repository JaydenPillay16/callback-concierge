output "callback_api_url" {
  description = "Base URL for the Callback Concierge API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}