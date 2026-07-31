# Worked example

## Input (destroy plan)

```hcl
Terraform will perform the following actions:

  # module.example_module.aws_iam_role.this will be destroyed
  - resource "aws_iam_role" "this" {
      - arn                   = "arn:aws:iam::123456789012:role/example-lambda-role" -> null
      - assume_role_policy    = jsonencode(
            {
              - Statement = [
                  - {
                      - Action    = "sts:AssumeRole"
                      - Effect    = "Allow"
                      - Principal = {
                          - Service = "lambda.amazonaws.com"
                        }
                    },
                ]
              - Version   = "2012-10-17"
            }
        ) -> null
      - create_date           = "2026-01-01T00:00:00Z" -> null
      - id                    = "example-lambda-role" -> null
      - name                  = "example-lambda-role" -> null
      - unique_id             = "AROAEXAMPLEID1234567" -> null
    }

  # module.example_module.aws_lambda_function.this will be destroyed
  - resource "aws_lambda_function" "this" {
      - arn            = "arn:aws:lambda:ap-northeast-1:123456789012:function:example-function" -> null
      - code_sha256    = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" -> null
      - function_name  = "example-function" -> null
      - handler        = "lambda_function.lambda_handler" -> null
      - role           = "arn:aws:iam::123456789012:role/example-lambda-role" -> null
      - runtime        = "python3.14" -> null
      - source_code_hash = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" -> null
    }

Plan: 0 to add, 0 to change, 2 to destroy.
```

## Output (inverted create plan)

```hcl
Terraform will perform the following actions:

  # module.example_module.aws_iam_role.this will be created
  + resource "aws_iam_role" "this" {
      + arn                = (known after apply)
      + assume_role_policy = jsonencode(
            {
              + Statement = [
                  + {
                      + Action    = "sts:AssumeRole"
                      + Effect    = "Allow"
                      + Principal = {
                          + Service = "lambda.amazonaws.com"
                        }
                    },
                ]
              + Version   = "2012-10-17"
            }
        )
      + create_date        = (known after apply)
      + id                 = (known after apply)
      + name               = "example-lambda-role"
      + unique_id          = (known after apply)
    }

  # module.example_module.aws_lambda_function.this will be created
  + resource "aws_lambda_function" "this" {
      + arn               = (known after apply)
      + code_sha256       = (known after apply)
      + function_name     = "example-function"
      + handler           = "lambda_function.lambda_handler"
      + role              = (known after apply)
      + runtime           = "python3.14"
      + source_code_hash  = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    }

Plan: 2 to add, 0 to change, 0 to destroy.
```

## Why each attribute landed where it did

- `arn`, `create_date`, `id`, `unique_id` on the IAM role: AWS assigns these when the role is
  actually created — unknowable before apply. → `(known after apply)`.
- `assume_role_policy`, `name`: written by the user/module in `.tf` config — Terraform knows
  these before touching AWS at all. → keep literal.
- `arn`, `code_sha256` on the Lambda function: provider-computed (ARN at creation, checksum
  computed by AWS from the uploaded package after upload). → `(known after apply)`.
- `role`: in config this is `aws_iam_role.this.arn` — a reference to a resource being created in
  the *same* plan, so even though the destroy diff shows a concrete ARN, a fresh create plan
  can't know it yet. → `(known after apply)`, not the literal value shown in the destroy diff.
  (Same reasoning applies to any account ID, resource name, or identifier appearing in a real
  destroy diff — treat them as sanitized example values here, not literal infrastructure facts.)
- `function_name`, `handler`, `runtime`: literal config values (`function_name = "..."`,
  `handler = "..."`, `runtime = "..."` in the `.tf` file). → keep literal.
- `source_code_hash`: this looks like a checksum (same value as `code_sha256` here) but it's
  actually supplied by config via `data.archive_file.this.output_base64sha256` — a data source
  read during `plan`, so it IS known before apply. Don't confuse it with `code_sha256`, which is
  the *provider's* computed checksum of what actually got uploaded.
