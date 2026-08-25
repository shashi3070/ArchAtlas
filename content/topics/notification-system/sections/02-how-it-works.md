# How It Works
1. **Event source**: application emits an event (e.g., 'order shipped').
2. **Notification service**: matches event to templates, applies user preferences.
3. **Channel routing**: determines which channels to use (push + email + SMS).
4. **Priority queue**: critical notifications (password reset) bypass regular queue.
5. **Delivery workers**: consume from queue; call channel APIs (APNs, SES, Twilio).
6. **Status tracking**: update delivery status (sent, delivered, opened, failed).

Components: event consumer, template engine, preference store, priority queue, delivery workers, status tracker.
