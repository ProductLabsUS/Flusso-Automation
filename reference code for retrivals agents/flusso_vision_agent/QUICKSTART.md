# Flusso Vision Agent - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Install Dependencies

```bash
# Activate your virtual environment (if not already active)
venv\Scripts\activate  # Windows

# Install required packages
pip install -r requirements.txt
```

### Step 2: Configure API Key

1. Copy the example environment file:
```bash
copy .env.example .env
```

2. Edit `.env` and add your Pinecone API key:
```
PINECONE_API_KEY=pcsk_YOUR_ACTUAL_KEY_HERE
```

### Step 3: Run Your First Search

Create `test_search.py`:

```python
from agent import VisionAgent

# Initialize agent
agent = VisionAgent()

# Check database
stats = agent.get_stats()
print(f"Database has {stats['total_vectors']} products ready!")

# Search with an image
results = agent.search("your_image.jpg", top_k=3)

# Display results
for i, result in enumerate(results, 1):
    print(f"\n--- Match #{i} ---")
    print(agent.format_result(result))
```

Run it:
```bash
python test_search.py
```

## 📖 Common Use Cases

### 1. Simple Image Search

```python
from agent import VisionAgent

agent = VisionAgent()
results = agent.search("product_photo.jpg", top_k=5)

for result in results:
    meta = result['metadata']
    print(f"{meta['product_title']} - Score: {result['score']:.2%}")
```

### 2. Filtered Search

```python
# Search only Chrome finishes
results = agent.search(
    "faucet.jpg",
    top_k=10,
    filters={"finish": "Chrome"}
)
```

### 3. High-Confidence Only

```python
# Only show matches above 85% similarity
results = agent.search(
    "image.jpg",
    top_k=10,
    min_score=0.85
)
```

### 4. Category-Specific Search

```python
# Search only in Sink Faucets category
results = agent.search(
    "sink_faucet.jpg",
    filters={"product_category": "Sink Faucets"}
)
```

## 🎯 What You Get Back

Each result contains:

```python
{
    "id": "100_1000CP",           # Unique product ID
    "score": 0.9986,              # Similarity (0-1, higher = better)
    "metadata": {
        "model_no": "100.1000CP",
        "product_title": "Single Hole Bathroom Faucet",
        "finish": "Chrome",
        "product_category": "Sink Faucets",
        "sub_category": "Single Hole Sink Faucets",
        "list_price": 369,
        "map_price": 276.75,
        "image_url": "flussofaucets.com/...",
        "collection": "Serie 100",
        "keywords": "...",
        # ... and more
    }
}
```

## 💡 Pro Tips

1. **Similarity Scores**:
   - 0.95-1.00: Nearly identical
   - 0.85-0.95: Very similar (same product line)
   - 0.70-0.85: Similar style/category
   - Below 0.70: Different products

2. **Performance**:
   - First search loads CLIP model (~3 seconds)
   - Subsequent searches are fast (~50-200ms)
   - Use filters to speed up searches

3. **Best Practices**:
   - Use clear, well-lit product photos
   - Front-facing angles work best
   - Remove backgrounds for better accuracy

## 🔧 Troubleshooting

**Agent initialization fails?**
→ Check your Pinecone API key in `.env`

**Slow performance?**
→ First run loads CLIP model (one-time ~3 sec delay)
→ Enable GPU for 2-3x speedup

**No results?**
→ Try lowering `min_score` threshold
→ Remove or broaden filters

## 📞 Need Help?

- Read the full `README.md` for detailed documentation
- Check the `agent.py` file for all available methods
- Review the test examples for more patterns

---

**You're all set! Start searching! 🎉**
