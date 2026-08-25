# Patterns
- **Template engine**: Jinja2/Handlebars templates with variable substitution.
- **Preference store**: per-user channel and frequency preferences (Redis or DB).
- **Priority levels**: critical (immediate), high (within 1h), low (batch daily).
- **Rate limiting**: per-user and per-channel limits to prevent spam.
- **Fallback**: if push fails, try email; if email fails, try SMS.
- **Analytics**: track open rates, click rates, delivery rates per channel.
