terraform {
  backend "s3" {
    bucket         = "callback-concierge-terraform-state"
    key            = "callback-concierge/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "callback-concierge-terraform-locks"
    encrypt        = true
  }
}