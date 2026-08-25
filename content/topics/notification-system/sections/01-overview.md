# Overview
A notification system delivers messages across multiple channels: push (APNs, FCM), email (SES, SendGrid), SMS (Twilio), and in-app. Core challenges: reliable delivery, user preferences, rate limiting, and template management.

The system must handle millions of notifications per day with guaranteed delivery (at-least-once) and deduplication.
