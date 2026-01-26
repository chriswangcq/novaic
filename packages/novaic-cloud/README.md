# NovAIC Cloud

> Cloud Service — Authentication, subscriptions, and LLM API proxy

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

NovAIC Cloud provides backend services for the NovAIC platform:

- **User Authentication** — Registration, login, JWT tokens
- **Subscription Management** — Plans, quotas, billing
- **LLM API Proxy** — Secure proxy to Claude/GPT APIs
- **Usage Tracking** — Token counting, rate limiting

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       NovAIC Cloud                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │    Auth    │  │Subscription│  │ LLM Proxy  │  │   User    │  │
│  │   /auth/*  │  │   /sub/*   │  │  /llm/*    │  │  /user/*  │  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │
│         │              │               │               │         │
│         └──────────────┼───────────────┼───────────────┘         │
│                        │               │                         │
│                        ▼               ▼                         │
│              ┌──────────────┐  ┌──────────────┐                  │
│              │  PostgreSQL  │  │  Claude API  │                  │
│              │   Database   │  │   GPT API    │                  │
│              └──────────────┘  └──────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd packages/novaic-cloud

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp env.example .env
# Edit .env with your settings
```

## Configuration

Create a `.env` file:

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/novaic

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# LLM APIs
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key

# Stripe (optional)
STRIPE_SECRET_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret
```

## Quick Start

```bash
# Start the server
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Authentication

```http
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
→ {"access_token": "jwt...", "token_type": "bearer"}

# Refresh token
POST /api/auth/refresh
Authorization: Bearer <token>

# Logout
POST /api/auth/logout
Authorization: Bearer <token>
```

### User

```http
# Get profile
GET /api/user/profile
Authorization: Bearer <token>

# Update profile
PATCH /api/user/profile
Authorization: Bearer <token>
{
  "name": "New Name"
}

# Get usage stats
GET /api/user/usage
Authorization: Bearer <token>
```

### Subscription

```http
# Get current subscription
GET /api/subscription
Authorization: Bearer <token>

# Get available plans
GET /api/subscription/plans

# Subscribe to plan
POST /api/subscription/subscribe
Authorization: Bearer <token>
{
  "plan_id": "pro"
}

# Cancel subscription
POST /api/subscription/cancel
Authorization: Bearer <token>
```

### LLM Proxy

```http
# Chat completion
POST /api/llm/chat
Authorization: Bearer <token>
{
  "model": "claude-sonnet-4-20250514",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 1024
}

# Streaming chat
POST /api/llm/chat/stream
Authorization: Bearer <token>
{
  "model": "claude-sonnet-4-20250514",
  "messages": [...],
  "stream": true
}
```

### Health

```http
GET /
GET /api/health
```

## Project Structure

```
novaic-cloud/
├── api/
│   ├── __init__.py       # Router exports
│   ├── auth.py           # Authentication endpoints
│   ├── user.py           # User management
│   ├── subscription.py   # Subscription management
│   └── llm.py            # LLM API proxy
├── config.py             # Configuration
├── main.py               # Application entry
├── requirements.txt
└── env.example
```

## Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 | 10 messages/day, basic models |
| **Pro** | $9.99/mo | Unlimited messages, all models |
| **Team** | $29.99/user/mo | Pro + team features |

## Database Schema

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  password_hash VARCHAR NOT NULL,
  name VARCHAR,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  plan VARCHAR NOT NULL,
  status VARCHAR NOT NULL,
  started_at TIMESTAMP,
  expires_at TIMESTAMP
);

-- Usage
CREATE TABLE usage_records (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  tokens_in INTEGER,
  tokens_out INTEGER,
  model VARCHAR,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Rate Limiting

| Plan | Requests/min | Tokens/day |
|------|--------------|------------|
| Free | 10 | 10,000 |
| Pro | 60 | Unlimited |
| Team | 120 | Unlimited |

## Development

```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Format code
black .
isort .

# Type check
mypy .
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables (Production)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET` | Yes | Secret for JWT signing |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `OPENAI_API_KEY` | No | OpenAI API key (optional) |
| `STRIPE_SECRET_KEY` | No | Stripe API key (for payments) |

## Security

- Passwords hashed with bcrypt
- JWT tokens with expiration
- Rate limiting per user
- API key validation
- CORS configuration

## License

MIT
