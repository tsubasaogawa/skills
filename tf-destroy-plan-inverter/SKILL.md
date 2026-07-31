---
name: tf-destroy-plan-inverter
description: "Use this skill whenever the user has a `terraform destroy` (or `terraform plan -destroy`) HCL diff output — resources marked `will be destroyed` with `- attr = value -> null` lines and a `Plan: N to add, 0 to change, N to destroy.` summary — and wants to know what `terraform plan` would show if the same config were applied from a completely clean/empty state (no state file, no existing resources). Trigger for phrases like 'この destroy 結果から、まっさらな環境で plan したらどうなるか教えて', 'destroy の逆を机上でやって', 'plan 相当の出力を再現して', 'reverse this destroy plan into a create plan', or when the user pastes a destroy diff and asks what a fresh `terraform plan` would look like. This is a desk-check / thought-experiment tool: it NEVER runs `terraform plan`, `apply`, or `destroy`, and never touches real state or infrastructure — it only transforms the pasted text. Do NOT use this skill if the user actually wants to run a real `terraform plan` (that's a normal Bash/terraform task, not a text inversion), or if they haven't pasted a destroy-style diff to invert."
allowed-tools: "Read"
metadata:
  version: 0.0.1
---

# Terraform Destroy Plan Inverter

You reconstruct, on paper only, what `terraform plan` would print for a set of resources if they
were being **created** from nothing — using a `terraform destroy` plan as the source of truth for
what the resources currently look like. You never run Terraform. The whole point of this skill is
to give a fast, safe answer when actually running `plan` isn't worth it (dev environment already
torn down, no time to re-provision, just want a sanity check on what a from-scratch apply would
create).

## Why this works

A destroy plan and a from-scratch create plan describe the same resources, just at opposite ends
of their lifecycle. Every attribute in the destroy diff (`attr = value -> null`) was true about the
resource *after* it was created — which means it tells you almost everything a create plan would
show, except for one category: values that AWS (or whatever provider) only assigns *at* create
time. Those are unknown until apply, so a real `plan` renders them as `(known after apply)`. Get
that distinction right and the rest is a mechanical sign-flip.

## Input you should expect

A block of HCL-flavored diff text produced by `terraform destroy` (or `terraform plan -destroy`),
containing one or more `# <address> will be destroyed` resource blocks with `- ` prefixed
attributes ending in `-> null`, plus a trailing summary line like:

```
Plan: 0 to add, 0 to change, N to destroy.
```

## Transformation steps

1. **Flip the framing.** `will be destroyed` → `will be created`. The `-` sigil on every line
   becomes `+`. Drop the `-> null` suffix since a create plan just shows the value being set (or
   `(known after apply)` — see step 2).

2. **Classify every attribute** into one of three buckets, then render accordingly:

   - **Config-authored values** — the user (or the module) wrote this value explicitly in `.tf`
     files, `.tfvars`, or a default in the resource schema (name, path, memory_size, timeout,
     description, handler, runtime, static tags, policy documents built from `jsonencode`, block
     arguments like `ephemeral_storage.size`, etc). These are known *before* apply, because they
     come from configuration, not from the provider. Keep the literal value, just with `+`.
   - **Provider-computed values** — values only the AWS API assigns once the resource actually
     exists (ARNs, generated IDs, timestamps, checksums the provider computes, version numbers,
     anything documented as "Read-Only" / `Computed: true` in the provider). These render as
     `(known after apply)` in a real plan because Terraform can't know them yet. See
     `references/computed-attributes.md` for a working list of these per common AWS resource type
     — check it before guessing, and extend the reasoning (not just the list) to resource types
     not covered there: ask "would AWS only tell me this after the object exists?"
   - **Dependency-derived values** — attributes whose value is a reference to another resource
     that is *also* being created in this same plan (e.g. `aws_lambda_function.role` pointing at
     `aws_iam_role.this.arn`). Even though the destroy diff shows the literal ARN, a fresh create
     plan can't know it either, because the referenced resource doesn't exist yet. Treat these as
     `(known after apply)` too, unless the referenced resource already exists outside this plan
     (rare in a from-scratch scenario — usually everything in the destroy diff is being created
     together).

3. **Preserve nested/block structure.** Keep `jsonencode(...)` bodies, inline policy blocks,
   `environment { variables = {...} }` and similar nested blocks intact — only the leaf values
   inside them get reclassified per step 2. Static IAM policy JSON, env var literals, tag maps
   the user defined, etc. stay as real values, not `(known after apply)`.

4. **Rewrite the summary line.** `Plan: 0 to add, 0 to change, N to destroy.` becomes
   `Plan: N to add, 0 to change, 0 to destroy.` — same N, opposite direction.

5. **Present the result as an HCL code block**, formatted like real `terraform plan` output
   (`# <address> will be created`, `+ resource "<type>" "<name>" {`, indentation matching
   Terraform's own style), so it can be dropped into a ticket or chat as-is.

## Guardrails

- **Never run `terraform plan`, `apply`, `destroy`, `refresh`, or touch the backend/state.** This
  skill is a pure text transformation exercise. If the user actually wants to execute Terraform,
  say so and let them ask for that separately — don't silently do it "to double check."
  - This distinction is not a formality: this skill is intentionally reached for in situations
    where running the real command is unwanted (already-torn-down dev envs, cost/time
    constraints, or the user explicitly saying not to run it) — running it anyway would violate
    the reason they asked for a desk-check in the first place.
- If the destroy diff includes secrets or webhook URLs etc. embedded in resource attributes (e.g.
  a Lambda `environment.variables`), reproduce them as given — they were already present in the
  input the user provided, so removing or masking them isn't your call to make silently. Flag it
  only if something looks like it shouldn't have been pasted at all (e.g. a live credential),
  and let the user decide.
- If you're genuinely unsure whether an attribute is provider-computed or config-authored, check
  `references/computed-attributes.md` first; if the resource type isn't listed, reason from the
  provider's documented schema (or your general knowledge of that resource type) rather than
  guessing silently — and default to `(known after apply)` for anything that smells like an
  identifier, timestamp, checksum, or ARN, since that's the safer failure mode (a real plan would
  never show a false concrete value for those).

## Worked example

See `references/example.md` for a full destroy-diff-in / create-plan-out example (an IAM role +
inline policies + Lambda function), including the reasoning for why each attribute landed where
it did. Use it as a style reference for formatting and the depth of computed-attribute reasoning
expected.
