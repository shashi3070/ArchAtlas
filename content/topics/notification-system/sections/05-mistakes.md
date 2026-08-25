# Common Mistakes
- **No user preferences**: sending notifications users didn't opt into.
- **No rate limiting**: users receive 50 notifications in an hour.
- **Ignoring delivery failures**: failed notifications are not retried or logged.
- **Hardcoded templates**: changing notification text requires a code deploy.
- **No A/B testing**: notification content and timing are not optimized.
