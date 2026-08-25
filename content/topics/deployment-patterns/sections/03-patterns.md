# Patterns
- **Database migration compatibility**: old code must work with new schema during rolling deploys; use expand-contract pattern.
- **Traffic mirroring**: shadow traffic to the new version without serving it to users; compare responses offline.
- **Automated rollback**: if canary error rate exceeds threshold, automatically shift traffic back.
- **Kill switch**: feature flag that immediately disables a problematic feature without a deploy.
- **Progressive delivery**: combine canary + automated analysis + rollback for zero-touch releases.
