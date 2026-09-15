resource "aws_dynamodb_table" "callback_requests" {
  name         = "callback-concierge-requests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "callbackId"

  attribute {
    name = "callbackId"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "S"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    range_key       = "createdAt"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}