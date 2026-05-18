# Implement Gemini multimodal content conversion

## Problem

GoogleProvider needs to convert OpenAI-style list content into Gemini parts instead of stringifying it.

## Success Criteria

- Text items become `{"text": ...}` parts.
- Data URL `image_url` items become inline image parts.
- Image base64 is not inserted into text parts.
- Plain string behavior remains unchanged.
