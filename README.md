# Callback Concierge

Serverless callback management solution built using AWS and Amazon Connect.

## Project Overview

Callback Concierge allows a customer calling through Amazon Connect to request a callback instead of waiting in the queue.

The solution captures the customer's phone number and reason for the callback, stores the request in DynamoDB, and processes pending callbacks through a scheduled Lambda function.

A supervisor-facing REST API provides visibility into pending callback requests.

## Technology Stack

- AWS Lambda
- Amazon DynamoDB
- Amazon API Gateway
- Amazon Connect
- AWS IAM
- Amazon CloudWatch
- Terraform
- AWS CDK
- Python

## Project Structure

```text
terraform/              Infrastructure as Code
lambda/                 Lambda functions
cdk/                    AWS CDK implementation
tests/                  Unit tests
docs/                   Architecture and project documentation


We'll continuously improve this as we build.

---

# 5. Create HANDOVER.md

Create:

```text
HANDOVER.md

# Callback Concierge — Handover

## Architecture

To be completed.

## Deployment

To be completed.

## Known Limitations

To be completed.

## Future Improvements

To be completed.