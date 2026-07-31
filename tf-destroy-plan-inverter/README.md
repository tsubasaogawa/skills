# Terraform Destroy Plan Inverter Skill

This repository contains the `tf-destroy-plan-inverter` skill for the AI Agent.
It takes a `terraform destroy` HCL diff and reconstructs, purely as a desk-check, what
`terraform plan` would show if the same resources were created from a completely clean/empty
state — without ever running `terraform plan`, `apply`, or `destroy`.

## Example

```console
✦ I will activate the tf-destroy-plan-inverter skill and invert the destroy diff into a create plan.

✦ Classifying attributes: `arn`/`create_date`/`id`/`unique_id` are provider-computed
  → (known after apply). `name`/`assume_role_policy` are config-authored → kept literal.
  `role` on the Lambda references the IAM role created in the same plan → (known after apply)
  even though the destroy diff shows a concrete ARN.

✦ Here is the equivalent create plan:

   Plan: 2 to add, 0 to change, 0 to destroy.
```

## Features

- **Pure text transformation**: never executes Terraform, never touches state or real infra.
- **Attribute classification**: distinguishes config-authored values (kept literal),
  provider-computed values, and dependency-derived values (both rendered as
  `(known after apply)`), backed by `references/computed-attributes.md` for common AWS resource
  types.
- **Realistic formatting**: output matches real `terraform plan` HCL styling so it can be pasted
  directly into a ticket or chat.

## Usage

To use this skill with the Agent:

1. Ensure you are in this repository or have the skill configured in your agent's path.
2. Paste a `terraform destroy` (or `terraform plan -destroy`) HCL diff and ask, e.g.:
   > "この destroy 結果から、まっさらな環境で plan したらどうなるか教えて"
   > "reverse this destroy plan into a create plan"
3. The agent will activate the `tf-destroy-plan-inverter` skill and return the inverted plan
   output — no real Terraform command is run.

## Skill Definition

The skill definition is this directory's `SKILL.md`. Deploy it to your agent's skills path
(e.g. `~/.claude/skills/tf-destroy-plan-inverter/`) the same way other skills in this repo are
deployed.
