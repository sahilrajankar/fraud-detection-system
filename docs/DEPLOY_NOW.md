# 🚀 Deploy in 5 Minutes

## Quick Deploy to Hugging Face Spaces (FREE)

---

### Step 1: Get Hugging Face Account (1 min)

**If you don't have one:**
- Go to: https://huggingface.co/join
- Sign up (email or GitHub)

**If you have one:**
- Go to: https://huggingface.co/settings/tokens
- Create new token (name: `deploy`, type: WRITE)
- **Copy the token** (you'll need it)

---

### Step 2: Run Deployment Script (1 min)

```powershell
cd d:\update
.\deploy_to_huggingface.ps1 -HF_USERNAME "your_hf_username"
```

Replace `your_hf_username` with your actual Hugging Face username.

---

### Step 3: Create Space on Hugging Face (1 min)

1. Go to: https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Name**: `fraud-detection-system`
   - **SDK**: Gradio
   - **Hardware**: CPU (free)
   - **Visibility**: Public (or Private)
4. Click **"Create Space"**

---

### Step 4: Push to Hugging Face (1 min)

The script will create `deployment_hf/` directory. Now push:

```powershell
cd deployment_hf
git push -u origin main
```

**When asked:**
- **Username**: your_hf_username
- **Password**: [PASTE YOUR ACCESS TOKEN from Step 1]

---

### Step 5: Wait for Build (2 min)

- Go to: https://huggingface.co/spaces/YOUR_USERNAME/fraud-detection-system
- Watch the build logs
- Wait for "Running" status

---

## ✅ Done!

Your app is live at:
```
https://huggingface.co/spaces/YOUR_USERNAME/fraud-detection-system
```

**Share this link everywhere!** 🎉

---

## 🎯 What You Get

A beautiful web interface with:
- ✅ 4 interactive tabs
- ✅ JSON text areas for input
- ✅ Instant fraud predictions
- ✅ Beautiful formatted results
- ✅ No coding required for users
- ✅ Shareable URL

---

## 🆘 Troubleshooting

**Build fails?**
- Check logs in Hugging Face Space
- Ensure models are in `models/` folder
- Ensure `src/` folder is present

**Can't push?**
- Make sure you created the Space first
- Use access token, not password
- Check username is correct

**Need help?**
- See: `HUGGINGFACE_DEPLOYMENT.md` for detailed guide

---

## 💡 Test Locally First?

```powershell
cd d:\update
python app.py
# Open: http://localhost:7860
```

---

**Ready? Run the script now!** 🚀

```powershell
cd d:\update
.\deploy_to_huggingface.ps1 -HF_USERNAME "your_username"
```
