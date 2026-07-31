# Provider-computed attributes by resource type (AWS)

Attributes here are only known once the provider has actually created the object, so a real
`terraform plan` for a *new* resource renders them as `(known after apply)` regardless of what
the destroy diff shows. This list covers commonly seen resource types — it is not exhaustive.
For anything not listed, check the resource's provider docs (marked "Read-Only" / not settable
as an argument) or reason from first principles: "does AWS assign this, or did the user write it
in config?"

## aws_iam_role
- `arn`, `id`, `create_date`, `unique_id`
- `managed_policy_arns` (list is empty/known if the config attaches none, but treat as
  `(known after apply)` if config attaches any managed policies by reference)
- Config-authored (keep literal): `name`, `path`, `assume_role_policy`, `max_session_duration`,
  `force_detach_policies`, `tags`/`tags_all`, `inline_policy` blocks (name + policy are literal
  JSON from config)

## aws_iam_role_policy / aws_iam_role_policy_attachment
- `id` (composite of role name + policy name — only fully known after the role exists if the
  role is also being created in this plan; treat as `(known after apply)`)
- Config-authored: `name`, `policy` (the JSON body), `role` (literal string if hardcoded, or
  `(known after apply)` if it references another resource being created, e.g. `aws_iam_role.this.name`)

## aws_lambda_function
- `arn`, `qualified_arn`, `invoke_arn`, `qualified_invoke_arn`, `response_streaming_invoke_arn`
- `id` (same as `function_name`, but Terraform still shows this as known-after-apply for a new
  resource in practice — verify against actual plan output if unsure)
- `last_modified`, `version`, `source_code_size`
- `code_sha256` (computed by AWS from the uploaded package; different from `source_code_hash`,
  which the user/module supplies from `data.archive_file` and IS known at plan time)
- `architectures`, `layers` (known-after-apply unless explicitly set in config — if config sets
  `architectures = ["x86_64"]`, keep the literal since it's config-authored)
- `role` — `(known after apply)` if it references an IAM role created in the same plan
- Config-authored (keep literal): `function_name`, `description`, `handler`, `runtime`,
  `memory_size`, `timeout`, `package_type`, `publish`, `reserved_concurrent_executions`,
  `skip_destroy`, `filename`, `source_code_hash` (from data source), `region`, `tags`/`tags_all`,
  `environment.variables` (literal env var map from config/tfvars), `ephemeral_storage.size`
  (config or provider default), `logging_config.log_format` / `log_group` (config or
  computed default that's still knowable pre-apply), `tracing_config.mode`

## aws_s3_bucket
- `arn`, `id`, `bucket_domain_name`, `bucket_regional_domain_name`, `hosted_zone_id`, `region`
- Config-authored: `bucket` (name), `tags`, `force_destroy`

## aws_security_group
- `arn`, `id`, `owner_id`
- Config-authored: `name`, `description`, `vpc_id`, `ingress`/`egress` rule blocks (literal from
  config), `tags`

## aws_dynamodb_table
- `arn`, `id`, `stream_arn`, `stream_label`
- Config-authored: `name`, `billing_mode`, `hash_key`, `range_key`, `attribute` blocks, `tags`

## General heuristic when a resource type isn't listed

Ask, for each attribute:

1. Did the user/module write this value in `.tf`/`.tfvars`, or does it have a static default in
   the resource schema? → config-authored, keep the literal.
2. Does it look like an identifier, ARN, timestamp, checksum/hash the *provider* computes, or a
   version/revision number? → provider-computed, render `(known after apply)`.
3. Does it reference another resource's attribute (`aws_x.y.arn`, `aws_x.y.id`, etc.) where that
   other resource is also being created in this same plan? → dependency-derived, render
   `(known after apply)`, even if the destroy diff shows a concrete value.
