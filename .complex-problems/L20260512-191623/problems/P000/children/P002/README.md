# Factory logs must show image delivery without raw base64

## Problem

Factory request logs currently store whatever request body is sent. If provider-native image data is present, logs/UI can become huge and misleading, while if image data is missing the UI does not make that absence explicit enough. Add log-only redaction so image delivery remains inspectable without dumping raw base64.

## Success Criteria

- Factory log snapshot keeps provider transport untouched.
- Logged messages replace `image_url.url` data URLs with metadata placeholders.
- Logged messages replace Anthropic-style image source data with metadata placeholders.
- Tests prove raw base64 is absent from the logged request body while image markers remain visible.
