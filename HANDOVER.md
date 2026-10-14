# Callback Concierge — Handover

## 1. Purpose

Callback Concierge is a serverless callback management solution that integrates Amazon Connect, AWS Lambda, and DynamoDB.

It allows a caller to request a callback through an Amazon Connect contact flow. The request is stored in DynamoDB, and the processing Lambda creates an Amazon Connect task for eligible requests.

This document records the architecture, deployment approach, current implementation state, known limitations, and recommended next steps.

## 2. Architecture

### Components

| Component | Responsibility |
|---|---|
| Amazon Connect inbound contact flow | Interacts with the caller and captures the callback reason. |
| `create_callback` Lambda | Validates and persists callback requests. |
| DynamoDB `callback-concierge-requests` | Stores callback details and processing status. |
| `process_callbacks` Lambda | Finds eligible pending requests and creates Connect tasks. |
| Amazon Connect task contact flow | Routes created tasks to the Callback Concierge Queue. |
| Callback Concierge Queue | Receives tasks for customer service follow-up. |
| Amazon EventBridge | Intended to invoke the processor on a schedule; schedule not yet enabled. |
| Amazon CloudWatch | Provides Lambda logs and supports planned alarms and metrics. |
| API Gateway and AWS CDK | Planned implementation for the supervisor-facing API. |

### Data flow

1. A customer calls the Amazon Connect number.
2. The inbound contact flow collects the callback reason.
3. The create-callback Lambda stores the request in DynamoDB.
4. The processing Lambda queries pending records.
5. The processor skips requests that are not explicitly eligible.
6. An eligible request is conditionally claimed and marked `PROCESSING`.
7. The processor calls Amazon Connect to create a task.
8. The record is updated to `CONTACT_CREATED` and the Connect contact ID is stored.
9. The task is routed to the Callback Concierge Queue for an agent to handle.

**Important:** Task creation is not the same as completing an outbound callback. Agent handling and the actual return call must be verified separately.

## 3. AWS Environment

The following are environment details from the current development setup. Confirm them against the active AWS account and configuration before making changes.

| Setting | Current development value |
|---|---|
| Core infrastructure region | `eu-west-1` |
| Amazon Connect region | `eu-west-2` |
| DynamoDB table | `callback-concierge-requests` |
| Connect instance name | `voiceidprototype` |
| Connect queue | `Callback Concierge Queue` |
| Task contact flow | `Callback Concierge Task Flow` |
| Processing Lambda | `callback-concierge-process-callbacks` |

The Amazon Connect instance is shared with the development sandbox. Avoid modifying unrelated queues, phone numbers, contact flows, or other shared resources.

Do not store credentials or secrets in this document.

## 4. Deployment

### Prerequisites

- An authorised AWS CLI profile or session.
- Python and the project's test dependencies.
- Terraform.
- Node.js and npm for the CDK component.
- Access to the required AWS resources.
- Correct environment-specific resource identifiers.

### Terraform workflow

From the repository root:

```powershell
cd terraform
terraform init
terraform validate
terraform plan
```

Review the plan for unexpected changes, especially deletions or modifications to shared Amazon Connect resources.

If the plan is correct and deployment is authorised:

```powershell
terraform apply
```

Return to the repository root when finished:

```powershell
cd ..
```

### Lambda configuration

The processing Lambda currently uses these environment variables:

| Variable | Purpose |
|---|---|
| `TABLE_NAME` | DynamoDB table containing callback requests. |
| `CONNECT_INSTANCE_ID` | Amazon Connect instance identifier. |
| `CONNECT_CONTACT_FLOW_ID` | Task contact flow identifier. |
| `CONNECT_REGION` | Region in which the Connect instance resides. |
| `PROCESS_ELIGIBLE_ONLY` | When `true`, only explicitly eligible callbacks are processed. |

The current deployment has `PROCESS_ELIGIBLE_ONLY=true`.

Ensure deployment packages contain the latest source code. When Terraform manages the Lambda package, make source changes first, review the generated plan, and verify the deployed function configuration afterward.

### Testing

Run the unit tests from the repository root:

```powershell
python -m pytest -v
```

The latest recorded test run completed with eight passing tests.

A successful unit test run does not prove that every AWS integration works. Use controlled end-to-end tests to verify DynamoDB updates, Amazon Connect task creation, task routing, and agent handling.

## 5. Current Processing Safeguards

### Eligibility

The processor skips records unless `processingEligible` is explicitly set to the Boolean value `true`, when eligibility-only processing is enabled.

Older callback records without this attribute remain ineligible. Do not bulk-mark existing records as eligible without confirming that they are safe and intended to be processed.

The create-callback workflow must be updated and tested so new valid callback requests are marked eligible before scheduled processing is enabled.

### Conditional claiming

The processor attempts to change a callback from `PENDING` to `PROCESSING` using a DynamoDB conditional update. This prevents concurrent executions from both successfully claiming the same record.

The processor also supplies the callback ID as the Amazon Connect task's client token to support idempotent task creation.

These safeguards reduce duplicate-processing risk, but they do not eliminate every failure scenario.

### Failure recovery

A failure after a callback has been marked `PROCESSING` can leave the record in that state. A failure after Amazon Connect creates a task but before DynamoDB records `CONTACT_CREATED` also requires careful recovery.

Before production use, implement and test a recovery strategy that reconciles callback records with existing Connect tasks. Avoid blindly resetting records to `PENDING`, as that could create duplicate work.

## 6. Known Limitations

- EventBridge scheduled processing has not yet been enabled.
- The creation Lambda does not yet mark new requests as eligible, so the current processor skips new records unless eligibility is deliberately added.
- Older pending records exist and must remain protected until reviewed.
- Recovery of callbacks stuck in `PROCESSING` needs further implementation.
- The system records task creation, not proof that an agent completed the return call.
- The supervisor-facing `GET /callbacks` API and CDK implementation remain outstanding.
- CloudWatch alarms and final operational metrics still need to be configured and verified.
- End-to-end tests do not replace the current unit test suite and should be expanded.
- The Amazon Connect development instance is shared; changes must be scoped carefully.

## 7. Recommended Next Steps

### Priority 1 — Complete eligibility handling

- Update the create-callback Lambda to set `processingEligible=true` for validated, new requests.
- Add unit tests for eligibility.
- Verify that older pending records remain ineligible.
- Deploy and inspect a controlled test request.

### Priority 2 — Complete scheduled processing

- Add an EventBridge schedule through Terraform.
- Configure the necessary invocation permissions.
- Keep the schedule disabled until the eligibility workflow is verified.
- Test one controlled callback before enabling recurring execution.
- Confirm the resulting DynamoDB status and Amazon Connect task.
- Verify that ineligible callbacks are skipped.

### Priority 3 — Improve reliability

- Design recovery for records stuck in `PROCESSING`.
- Handle the case where Connect task creation succeeds but the DynamoDB status update fails.
- Review retry behaviour and task idempotency.
- Add appropriate metrics, alarms, and actionable log messages.

### Priority 4 — Build the supervisor API

- Implement `GET /callbacks` using API Gateway and Lambda.
- Return useful callback information with appropriate filtering and error handling.
- Rebuild the supervisor API infrastructure using AWS CDK.
- Compare the CDK implementation with the existing Terraform-managed resources without overlapping ownership.

### Priority 5 — Finalise documentation and handover

- Document the final architecture and deployed resources.
- Record verified deployment and rollback procedures.
- Complete end-to-end validation.
- Add the final CloudWatch alarm configuration.
- Update the README status table to reflect completed work.

## 8. Operational Safety

Before any deployment or test:

1. Confirm the active AWS account and region.
2. Inspect the Terraform plan.
3. Identify whether the test could create a real Amazon Connect task.
4. Use a controlled test callback with an approved test number.
5. Confirm the record is eligible before invoking the processor.
6. Verify the result in DynamoDB and Amazon Connect.
7. Avoid modifying unrelated resources in the shared development environment.

Never commit AWS credentials, sensitive customer information, or local secret files.

## 9. Verification Record

The following items have been verified during development:

- The inbound Amazon Connect callback flow was live-tested.
- The create-callback Lambda stored a test callback in DynamoDB.
- The processor created a controlled Amazon Connect task.
- The resulting callback record reached `CONTACT_CREATED`.
- The processor's eligibility protection was deployed.
- Twelve older pending callbacks were observed without `processingEligible=true` and were left untouched.
- The latest recorded Python unit test run passed all eight tests.
- The eligibility improvements were committed and pushed to the `main` branch.

The EventBridge schedule, supervisor API, CDK implementation, and final production-readiness checks remain outstanding.

## 10. Repository

GitHub: https://github.com/JaydenPillay16/callback-concierge

**Handover status:** Core callback flow and controlled task creation are implemented. Scheduled automation and supervisor-facing functionality remain in progress.
