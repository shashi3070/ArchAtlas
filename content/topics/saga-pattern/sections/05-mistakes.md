# Common Mistakes
- **Missing compensation**: a step completes but its compensating transaction is not implemented.
- **Non-idempotent steps**: retries create duplicate side effects.
- **No semantic lock**: concurrent operations on the same entity during a saga cause race conditions.
- **Infinite saga loops**: compensation triggers another compensation in an infinite loop.
- **No timeout**: a saga hangs forever waiting for a step that will never complete.
