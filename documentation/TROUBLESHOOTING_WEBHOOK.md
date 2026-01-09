# Webhook Troubleshooting Guide - Cloud Run

## Issue: Webhook Not Reaching Application

If you see startup logs but NO webhook processing logs (no "📬 Webhook received"), follow these steps:

---

## Step 1: Check Cloud Run Authentication

**Cloud Run blocks unauthenticated requests by default.** Freshdesk cannot authenticate, so you must allow public access.

### Fix Authentication:
```bash
# Allow unauthenticated invocations
gcloud run services add-iam-policy-binding YOUR-SERVICE-NAME \
  --region=YOUR-REGION \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### Or use Console:
1. Go to Cloud Run console
2. Select your service
3. Click "SECURITY" tab
4. Select "Allow unauthenticated invocations"
5. Click "SAVE"

---

## Step 2: Verify Webhook URL in Freshdesk

Your webhook URL should be:
```
https://YOUR-SERVICE-NAME-xxxxx.run.app/webhook
```

**NOT:**
- ~~https://YOUR-SERVICE-NAME-xxxxx.run.app~~ (missing /webhook)
- ~~https://YOUR-SERVICE-NAME-xxxxx.run.app/~~ (missing webhook)

### To Configure in Freshdesk:
1. Go to Admin Settings → Workflows → Automations
2. Create "Ticket is Created" rule
3. Add action: "Trigger Webhook"
4. **URL:** `https://YOUR-SERVICE-NAME.run.app/webhook`
5. **Method:** POST
6. **Content Type:** JSON
7. **Payload:**
   ```json
   {
     "ticket_id": "{{ticket.id}}",
     "ticket": {
       "id": "{{ticket.id}}",
       "subject": "{{ticket.subject}}",
       "description": "{{ticket.description}}",
       "status": "{{ticket.status}}",
       "priority": "{{ticket.priority}}",
       "requester_email": "{{ticket.requester.email}}",
       "tags": {{ticket.tags | json}}
     }
   }
   ```

---

## Step 3: Test Webhook Manually

Test your Cloud Run endpoint directly:

```bash
# Replace with your actual Cloud Run URL
curl -X POST https://YOUR-SERVICE-NAME.run.app/webhook \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "12345"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "ticket_id": "12345",
  ...
}
```

If you get **403 Forbidden** → Authentication issue (see Step 1)
If you get **404 Not Found** → Wrong URL path (add /webhook)
If you get **200 OK** → Webhook is working! Check Freshdesk configuration

---

## Step 4: Check Cloud Run Logs

View detailed logs to see what's happening:

```bash
# View logs in terminal
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=YOUR-SERVICE-NAME" \
  --limit 50 \
  --format "table(timestamp, textPayload)"

# Or view in console:
# https://console.cloud.google.com/logs/query?project=YOUR-PROJECT
```

### What to Look For:

✅ **Good logs** (webhook working):
```
📬 Webhook received: {...}
🎫 Processing ticket #12345 with ReACT agent...
✅ Workflow completed for ticket #12345
```

❌ **Bad logs** (authentication blocking):
```
403 Forbidden
Unauthorized request
Missing or invalid authorization header
```

❌ **Bad logs** (wrong path):
```
404 Not Found
```

---

## Step 5: Verify Cloud Run Service Status

```bash
# Check service status
gcloud run services describe YOUR-SERVICE-NAME --region=YOUR-REGION

# Look for:
# ✓ status: Ready
# ✓ URL: https://...run.app
# ✓ Ingress: all
# ✓ Authentication: allow-unauthenticated (if properly configured)
```

---

## Common Issues & Solutions

### Issue: 403 Forbidden
**Cause:** Cloud Run requires authentication, Freshdesk cannot authenticate
**Solution:** Run Step 1 (allow unauthenticated invocations)

### Issue: 404 Not Found
**Cause:** Wrong endpoint path
**Solution:** Add `/webhook` to the URL in Freshdesk configuration

### Issue: Logs show "Webhook received" but then timeout
**Cause:** Missing environment variables (API keys)
**Solution:** Check Secret Manager configuration in cloudbuild.yaml

### Issue: No logs at all
**Cause 1:** Service crashed during startup
**Solution:** Check startup logs for errors
**Cause 2:** Freshdesk webhook not configured
**Solution:** Verify webhook automation rule is active in Freshdesk

---

## Quick Checklist

- [ ] Cloud Run service is deployed and running
- [ ] Service allows unauthenticated invocations
- [ ] Freshdesk webhook URL ends with `/webhook`
- [ ] Freshdesk webhook method is POST
- [ ] Freshdesk webhook content type is JSON
- [ ] Manual curl test returns 200 OK
- [ ] Logs show "📬 Webhook received" when test ticket created

---

## Debug Mode: Add Logging

If you still don't see webhooks, add verbose logging to catch ALL requests:

### Add Middleware to main_react.py:

```python
@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    logger.info(f"🔍 Incoming request: {request.method} {request.url.path}")
    logger.info(f"🔍 Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"🔍 Response status: {response.status_code}")
    return response
```

This will log EVERY request that reaches your service, even before endpoint routing.

---

## Need More Help?

1. **Check actual Cloud Run URL:**
   ```bash
   gcloud run services describe YOUR-SERVICE-NAME --region=YOUR-REGION --format="value(status.url)"
   ```

2. **Check IAM policy:**
   ```bash
   gcloud run services get-iam-policy YOUR-SERVICE-NAME --region=YOUR-REGION
   ```
   Should show `allUsers` with `roles/run.invoker`

3. **Test with real Freshdesk ticket:**
   - Create a test ticket manually in Freshdesk
   - Check Cloud Run logs within 30 seconds
   - Look for "📬 Webhook received" log entry
