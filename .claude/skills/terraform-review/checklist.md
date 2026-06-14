<!-- Generated from .ai-common. Do not edit directly. -->

# Terraform Review Checklist

- No unapproved IAM expansion
- No secret values in code or state outputs
- Public exposure is intentional and documented
- Cloud Run, Firebase, GCS, and logging settings are cost-aware
- State backend is appropriate
- Destructive replacement is identified
- Plan output reviewed before apply
