# 🚀 Quick Start Guide - Live Agent Orchestrator

## ⚡ 3-Step Setup

### Step 1: Configure API Key
```bash
# Copy the template
cp .env.template .env

# Edit .env and add your key
# GEMINI_API_KEY=your_actual_api_key_here
```

Get your API key: https://makersuite.google.com/app/apikey

### Step 2: Verify Setup
```bash
python verify_setup.py
```

Expected output: `6/6 checks passed`

### Step 3: Run Live Test
```bash
python live_agent_orchestrator.py
```

---

## 📁 Key Files

| File | Purpose |
|:-----|:--------|
| `live_agent_orchestrator.py` | Main orchestrator (run this!) |
| `verify_setup.py` | Setup validation |
| `.env` | Your API key (create from `.env.template`) |
| `gemini_utils.py` | API utilities |
| `prompts.py` | Agent prompts |
| `README_LIVE_ORCHESTRATOR.md` | Full documentation |

---

## 🎯 What It Does

1. **Author Agent** generates a capstone project document
2. **Reviewer Agent** audits the document for quality
3. **Meta-Reviewer Agent** refines prompts based on feedback
4. Loop continues until document passes or max iterations reached

---

## 💰 Cost

~$0.01 USD per run (using `gemini-2.0-flash-exp`)

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
- Create `.env` file from `.env.template`
- Add your API key (no quotes, no spaces)

### "API call failed"
- Check API key is valid
- Verify you have quota/credits
- Check internet connection

### "Module not found"
- Run: `pip install -r requirements.txt`

---

## 📊 Current Status

✅ **4/6 checks passing**
- ✅ Python version compatible
- ✅ Dependencies installed
- ✅ File structure complete
- ✅ Scorecard parsing validated
- ❌ Need `.env` file with API key
- ❌ Need API connectivity test

---

## 📚 Full Documentation

See [README_LIVE_ORCHESTRATOR.md](file:///c:/Users/riccardo.bonazzi/Documents/GitHub/MAS_writer/README_LIVE_ORCHESTRATOR.md) for complete guide.
