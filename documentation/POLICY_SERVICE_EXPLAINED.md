# 📋 Policy Service - How It Works

## ✅ **NOW FULLY ACTIVATED**

The policy service is now initialized on application startup and works exactly as you described!

---

## 🔄 **How It Works End-to-End**

### **1. Startup (when server starts)**
```
App starts → init_policy_service() → Downloads from Google Docs → Caches policy → Starts background refresh thread (every 6 hours)
```

### **2. When Ticket Arrives**
```
Webhook → Planner Node → get_relevant_policy(ticket_category, ticket_text) → Returns relevant policy section
```

### **3. Planner Uses Policy to Make Smart Decisions**

**Example: Warranty Claim Request**

```python
# Planner receives ticket about warranty claim
ticket = {
    "subject": "My faucet is broken, warranty claim",
    "description": "Purchased 2 years ago, product model XYZ-123",
    "category": "warranty_claim"
}

# Planner calls policy service
policy = get_relevant_policy(
    ticket_category="warranty_claim",
    ticket_text="Purchased 2 years ago, product model XYZ-123"
)

# Policy service returns:
{
    "primary_section": """
    ### 1.2 Required Documents for Warranty Claim
    - ✅ Proof of purchase (receipt/invoice) - MANDATORY
    - ✅ Product model number
    - ✅ Photos of defect (recommended)
    - ✅ Purchase date must be within warranty period
    
    ### 1.1 Warranty Coverage
    - Standard warranty: 1 year from purchase date
    - Extended warranty (VIP customers): 2 years
    """,
    
    "policy_requirements": [
        "Proof of purchase (receipt/invoice) - MANDATORY",
        "Product model number",
        "Photos of defect (recommended)",
        "Purchase date must be within warranty period"
    ]
}

# Planner creates execution plan based on policy:
execution_plan = [
    {
        "step": 1,
        "tool": "attachment_analyzer_tool",
        "reason": "Policy requires proof of purchase - check if customer attached receipt"
    },
    {
        "step": 2,
        "tool": "product_search_tool",
        "reason": "Verify product model XYZ-123 exists and check warranty type"
    },
    # Planner knows: "purchased 2 years ago" > 1 year standard warranty
    # But checks if customer is VIP (2 year warranty) before rejecting
    {
        "step": 3,
        "decision": "If not VIP and no receipt showing 2-year warranty, deny claim"
    }
]
```

---

## 🎯 **Real Policy Examples from Your Document**

### **Example 1: Return Request**

**Customer says:** "I want to return this product, bought 60 days ago"

**Policy fetched:**
```
Return Policy Timeline:
- 0-45 days: 15% restocking fee
- 46-90 days: 25% restocking fee ← Customer is here!
- 91-180 days: 50% restocking fee

Required:
- ✅ RGA number (must request first)
- ✅ Proof of purchase with date
- ❌ Custom/special orders NOT returnable
```

**Planner decides:**
1. ✅ Check attachments for proof of purchase
2. ✅ Verify product is not custom order
3. ✅ Calculate: 25% restocking fee applies
4. ✅ Generate RGA number if approved
5. ❌ Don't waste time gathering product info if it's custom order (not returnable)

---

### **Example 2: Missing Parts**

**Customer says:** "My sink came without drain parts, ordered 2 months ago"

**Policy fetched:**
```
Missing Parts Policy:
- Must report within 30 days of delivery ← 2 months = 60 days!
- Free replacement if within 30 days
- After 30 days: Customer must purchase parts
```

**Planner decides:**
1. ❌ Don't process as "missing parts" (outside 30-day window)
2. ✅ Treat as "replacement parts" request
3. ✅ Quote paid parts pricing
4. ✅ Apologize for confusion about policy

---

### **Example 3: VIP Customer**

**Customer says:** "I'm a VIP, need warranty claim processed"

**Policy fetched:**
```
VIP Customer Special Rules:
- Always approve reasonable warranty claims
- Free shipping on ALL replacements
- Extended return window: 90 days full refund
- Can override standard policies
```

**Planner decides:**
1. ✅ Check if customer is actually VIP
2. ✅ Apply lenient approval criteria
3. ✅ Skip charging shipping fees
4. ✅ Prioritize this ticket

---

## 🔧 **Policy Document Structure**

Your Google Docs document should have sections like:

```markdown
# Company Policy Guide

## WARRANTY CLAIMS
- Coverage periods
- Required documents
- Approval criteria
- Exceptions

## RETURNS & REFUNDS
- Timeline and fees
- Required documents
- Non-returnable items

## REPLACEMENT PARTS
- Free vs paid
- Availability checks

## ESCALATION RULES
- When to escalate
- VIP handling
```

The service automatically:
- Parses sections by headers
- Matches ticket type to relevant section
- Extracts requirements (✅ checkmarks)
- Provides to planner for smart decisions

---

## 📊 **Current Status**

✅ **Policy Service:** ACTIVE and fully functional
✅ **Google Docs Sync:** Configured (ID: `1NYWE1ZnSQDgdRW0XtUt4eMggvJp7Rcp9XRrKXMQvfF0`)
✅ **Background Refresh:** Running (every 6 hours)
✅ **Planner Integration:** Working (uses policy in prompts)
✅ **Local Fallback:** Comprehensive backup policy available

---

## 🧪 **To Test It**

1. **Check logs at startup:**
   ```
   [POLICY_SERVICE] Initializing policy service...
   [POLICY_SERVICE] Downloading policy document...
   [POLICY_SERVICE] Downloaded policy doc: XXXX characters
   [POLICY_SERVICE] Parsed 5 policy sections: [...]
   [POLICY_SERVICE] Cache ready with 5 sections
   [POLICY_SERVICE] Background refresh thread started
   ```

2. **Check planner logs when processing ticket:**
   ```
   [PLANNER] Looking for policy sections: ['warranty']
   [PLANNER] Policy section: WARRANTY CLAIMS
   [PLANNER] Policy requirements: ['Proof of purchase - MANDATORY', 'Product model number']
   ```

3. **Verify Google Docs access:**
   - The document must be **publicly accessible** or **shared with service account**
   - URL format: `https://docs.google.com/document/d/DOC_ID/export?format=txt`

---

## 🚀 **Your System Now:**

**Before:** Planner blindly processed all requests
**Now:** Planner checks policy first, makes smart decisions about:
- What information is needed
- What steps to take
- When to deny/approve
- Special VIP handling
- When to escalate

Your workflow is now **policy-aware and intelligent**! 🎉
