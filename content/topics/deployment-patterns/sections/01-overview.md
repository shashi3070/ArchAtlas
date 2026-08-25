# Overview
Deployment patterns determine how new code reaches production and how quickly you can roll back if something goes wrong. The choice depends on your risk tolerance, infrastructure cost, and required rollback speed.

The progression from least to most sophisticated: big bang (all at once) → rolling (instance by instance) → canary (percentage-based) → blue-green (parallel environments) → feature flags (deploy + release separation).
