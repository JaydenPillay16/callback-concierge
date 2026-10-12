provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "CallbackConcierge"
      Environment = "Sandbox"
      ManagedBy   = "Terraform"
    }
  }
}

provider "aws" {
  alias  = "connect"
  region = "eu-west-2"

  default_tags {
    tags = {
      Project     = "CallbackConcierge"
      Environment = "Sandbox"
      ManagedBy   = "Terraform"
    }
  }
}