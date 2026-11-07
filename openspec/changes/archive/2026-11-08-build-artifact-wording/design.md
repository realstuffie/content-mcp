## Decision

Document the existing check. `get_rendered_rule` returns no result when the
per-rule JSON is absent, before it looks for OVAL or remediations. The
availability tool records false for that result. A readable JSON file makes
the flag true even without a datastream.

Only detected build directories can contribute an entry. A failed check can
also leave a product without an entry, so omission means there is no reported
result. It does not prove that the product is unbuilt or unsupported.

Broadening the check to every artifact would change the field's behavior and
would require a separate decision about partial or stale builds. That is
outside this wording fix.

## Verification

The test creates readable rule JSON for RHEL 9, OVAL and a Bash remediation
without rule JSON for RHEL 8, and no build for RHEL 10. The result is
`{"rhel8": false, "rhel9": true}`. No datastream is needed for the true entry.
