# Gold Tier Research

## Overview
This document contains research findings, API documentation references, and implementation notes for Gold Tier integrations.

---

## 1. Odoo Integration Research

### Odoo 19+ JSON-RPC API

**Documentation**: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html

#### Authentication
```python
import requests
import json

# JSON-RPC 2.0 authentication
def odoo_authenticate(url, db, username, password):
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "common",
            "method": "authenticate",
            "args": [db, username, password, {}]
        },
        "id": 1
    }
    
    response = requests.post(f"{url}/web/session/authenticate", json=payload)
    return response.json()
```

#### Key Models
- `account.move`: Invoices and bills
- `account.payment`: Payments
- `account.move.line`: Invoice lines
- `res.partner`: Customers and vendors
- `account.journal`: Journals
- `account.account`: Accounts

#### Create Invoice Example
```python
def create_invoice(url, db, uid, password, partner_id, lines):
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [
                db, uid, password,
                "account.move",
                "create",
                [{
                    "move_type": "out_invoice",
                    "partner_id": partner_id,
                    "invoice_line_ids": [(0, 0, line) for line in lines]
                }]
            ]
        },
        "id": 2
    }
    
    response = requests.post(f"{url}/web/dataset/call_kw", json=payload)
    return response.json()
```

#### Rate Limits
- No official rate limits for self-hosted
- Recommended: 100 calls/minute for stability
- Use batch operations where possible

---

## 2. Facebook Graph API Research

**Documentation**: https://developers.facebook.com/docs/graph-api/

### Authentication
- OAuth 2.0 flow
- Page Access Token required
- Token expiry: 60 days (extendable)

### Key Endpoints
```
GET /{page-id}                    # Page details
POST /{page-id}/feed             # Create post
GET /{post-id}                   # Post details
GET /{post-id}/comments          # Get comments
POST /{post-id}/comments         # Add comment
GET /{post-id}/insights          # Get metrics
```

### Post Creation Example
```python
import requests

def create_facebook_page_post(page_access_token, page_id, message, link=None):
    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    
    params = {
        "message": message,
        "access_token": page_access_token
    }
    
    if link:
        params["link"] = link
    
    response = requests.post(url, params=params)
    return response.json()
```

### Rate Limits
- 200 calls/hour per page
- 4,000 calls/hour per app
- Use exponential backoff on 429 errors

### Insights Metrics
- `post_impressions`: Total impressions
- `post_engagements`: Total engagements
- `post_clicks`: Link clicks
- `post_comments`: Comment count
- `post_shares`: Share count

---

## 3. Instagram Graph API Research

**Documentation**: https://developers.facebook.com/docs/instagram-api/

### Prerequisites
- Instagram Business Account
- Facebook Page connected
- Facebook App with Instagram Graph API permission

### Authentication
- Same as Facebook (Page Access Token)
- Instagram User ID required

### Key Endpoints
```
GET /{ig-user-id}/media          # Get media
POST /{ig-user-id}/media         # Create media container
POST /{ig-user-id}/media_publish # Publish media
GET /{ig-media-id}               # Get media details
GET /{ig-media-id}/insights      # Get metrics
GET /{ig-user-id}/stories        # Get stories
POST /{ig-user-id}/stories       # Create story
```

### Image Post Example
```python
def create_instagram_post(access_token, ig_user_id, image_url, caption):
    # Step 1: Create media container
    container_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
    container_params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    container_response = requests.post(container_url, params=container_params)
    container_id = container_response.json()["id"]
    
    # Step 2: Publish media
    publish_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
    publish_params = {
        "creation_id": container_id,
        "access_token": access_token
    }
    publish_response = requests.post(publish_url, params=publish_params)
    return publish_response.json()
```

### Rate Limits
- 200 calls/hour
- 25 media creations/day
- Use app-level rate limiting

### Insights Metrics
- `impressions`: Total impressions
- `reach`: Unique accounts reached
- `engagement`: Total engagements
- `saved`: Save count
- `comments`: Comment count

---

## 4. Twitter API v2 Research

**Documentation**: https://developer.twitter.com/en/docs/twitter-api

### Authentication
- OAuth 2.0 Bearer Token
- API Key + Secret required
- Access Token + Secret required

### Key Endpoints
```
POST /2/tweets                    # Create tweet
GET /2/tweets/:id                 # Get tweet
GET /2/users/:id/tweets          # Get user tweets
GET /2/users/:id/mentions        # Get mentions
POST /2/tweets/:id/liking        # Like tweet
POST /2/tweets/:id/retweeting    # Retweet
```

### Create Tweet Example
```python
import requests
import oauthlib

def create_tweet(bearer_token, tweet_text, media_ids=None):
    url = "https://api.twitter.com/2/tweets"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    payload = {"text": tweet_text}
    
    if media_ids:
        payload["media"] = {"media_ids": media_ids}
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

### Upload Media Example
```python
def upload_media(bearer_token, image_path):
    url = "https://upload.twitter.com/1.1/media/upload.json"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }
    
    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, headers=headers, files=files)
    
    return response.json()["media_id_string"]
```

### Rate Limits
- 300 tweets/day (new accounts)
- 2,400 tweets/day (established accounts)
- 50 mentions/hour
- 1,000 GET requests/15 minutes

### Engagement Metrics
- `public_metrics.like_count`
- `public_metrics.retweet_count`
- `public_metrics.reply_count`
- `public_metrics.quote_count`
- `public_metrics.impression_count`

---

## 5. Error Handling Patterns

### Exponential Backoff with Jitter
```python
import random
import time

def retry_with_backoff(func, max_retries=5, base_delay=1, max_delay=60):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)
            time.sleep(delay + jitter)
```

### Circuit Breaker Pattern
```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise
```

---

## 6. OAuth 2.0 Implementation Notes

### Generic OAuth Flow
```python
from requests_oauthlib import OAuth2Session

def oauth_authorize(client_id, client_secret, authorization_url, token_url, redirect_uri, scope):
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    
    # Get authorization URL
    authorization_url, state = oauth.authorization_url(authorization_url)
    print(f"Visit: {authorization_url}")
    
    # Get authorization code from user
    authorization_response = input("Enter redirect URL: ")
    
    # Fetch token
    token = oauth.fetch_token(
        token_url,
        authorization_response=authorization_response,
        client_secret=client_secret
    )
    
    return oauth, token
```

### Token Refresh
```python
def refresh_token(oauth, token_url, client_id, client_secret, refresh_token):
    token = oauth.refresh_token(
        token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token
    )
    return token
```

---

## 7. Security Best Practices

### Credential Storage
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class CredentialManager:
    def __init__(self, master_password: str, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()
```

### Audit Logging
```python
import json
import hashlib
from datetime import datetime

class AuditLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.last_hash = None
    
    def log(self, entry: dict):
        # Add timestamp
        entry["timestamp"] = datetime.utcnow().isoformat()
        
        # Add previous hash for tamper-evidence
        if self.last_hash:
            entry["previous_hash"] = self.last_hash
        
        # Calculate current hash
        entry_json = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        entry["current_hash"] = current_hash
        self.last_hash = current_hash
        
        # Append to log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## 8. Performance Optimization

### Connection Pooling
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_pool(base_url, pool_size=10):
    session = requests.Session()
    
    # Configure retry strategy
    retry = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_size,
        pool_maxsize=pool_size
    )
    
    session.mount(base_url, adapter)
    return session
```

### Async Operations
```python
import asyncio
import aiohttp

async def fetch_multiple_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]
```

---

## 9. Testing Strategies

### Mock API Responses
```python
from unittest.mock import Mock, patch

def test_odoo_integration():
    mock_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "id": 12345,
            "name": "INV/2026/00123"
        }
    }
    
    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        
        # Test code here
        result = odoo_create_invoice(...)
        
        assert result["id"] == 12345
```

### Integration Test Fixtures
```python
import pytest

@pytest.fixture
def odoo_config():
    return {
        "url": "http://test-odoo:8069",
        "database": "test_db",
        "username": "admin",
        "password": "admin"
    }

@pytest.fixture
def facebook_config():
    return {
        "app_id": "test_app_id",
        "app_secret": "test_app_secret",
        "access_token": "test_token",
        "page_id": "test_page_id"
    }
```

---

## 10. Deployment Considerations

### Docker Setup
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["python", "-m", "src.ai_employee_gold.autonomous_run"]
```

### Environment Variables
```bash
# Odoo
ODOO_URL=http://localhost:8069
ODOO_DATABASE=production
ODOO_USERNAME=admin
ODOO_API_KEY=your_api_key

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram
INSTAGRAM_USER_ID=your_user_id
INSTAGRAM_ACCESS_TOKEN=your_access_token

# Twitter
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Gold Tier Settings
GOLD_TIER_ENABLED=true
AUDIT_LOGGING_ENABLED=true
RALPH_WIGGUM_ENABLED=true
```

---

## 11. Troubleshooting Guide

### Common Issues

#### Odoo Connection Failed
- Check Odoo service is running
- Verify database name is correct
- Ensure API key has proper permissions
- Check firewall rules

#### Facebook/Instagram API Errors
- Verify App is in Live mode (not Development)
- Check Page Access Token has required permissions
- Ensure Instagram account is Business account
- Verify token hasn't expired

#### Twitter API Rate Limits
- Monitor `x-rate-limit-remaining` header
- Implement exponential backoff
- Consider applying for elevated access

#### Audit Log Corruption
- Hash chain verification fails
- Restore from backup
- Check disk space and permissions

---

## 12. References

### Official Documentation
- Odoo 19: https://www.odoo.com/documentation/19.0/
- Facebook Graph API: https://developers.facebook.com/docs/graph-api/
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api/
- Twitter API v2: https://developer.twitter.com/en/docs/twitter-api

### Libraries
- requests-oauthlib: https://requests-oauthlib.readthedocs.io/
- cryptography: https://cryptography.io/
- aiohttp: https://docs.aiohttp.org/

### Patterns
- Circuit Breaker: https://martinfowler.com/bliki/CircuitBreaker.html
- Exponential Backoff: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
