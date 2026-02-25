# 🔐 GitHub Authentication Instructions

## Issue
You're getting a "Permission denied" error when pushing to GitHub. This is because GitHub requires authentication.

## Solution: Use Personal Access Token

### Step 1: Create Personal Access Token

1. Go to GitHub: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `Major Project Push`
4. Select scopes:
   - ✅ **repo** (Full control of private repositories)
5. Click **"Generate token"**
6. **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)

### Step 2: Update Remote URL with Token

Run this command (replace `YOUR_TOKEN` with your actual token):

```bash
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project"
git remote set-url origin https://YOUR_TOKEN@github.com/shaik-kabeer/Major_project-.git
```

**OR** use your username:

```bash
git remote set-url origin https://shaik-kabeer:YOUR_TOKEN@github.com/shaik-kabeer/Major_project-.git
```

### Step 3: Push Again

```bash
git push -u origin main
```

When prompted for password, paste your **token** (not your GitHub password).

---

## Alternative: Use GitHub CLI (gh)

If you have GitHub CLI installed:

```bash
gh auth login
git push -u origin main
```

---

## Alternative: Use SSH (Recommended for Long-term)

### Step 1: Generate SSH Key

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### Step 2: Add SSH Key to GitHub

1. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to: https://github.com/settings/keys
3. Click **"New SSH key"**
4. Paste your public key
5. Save

### Step 3: Update Remote to SSH

```bash
git remote set-url origin git@github.com:shaik-kabeer/Major_project-.git
git push -u origin main
```

---

## Quick Fix (If You Just Want to Push Now)

1. **Get your token** from https://github.com/settings/tokens
2. **Run these commands**:

```bash
cd "C:\Users\Lenovo\Downloads\Collage_Materials\Major project"
git remote set-url origin https://YOUR_TOKEN@github.com/shaik-kabeer/Major_project-.git
git push -u origin main
```

Replace `YOUR_TOKEN` with your actual token when prompted or in the URL.

---

## Verify Remote URL

Check your remote URL:
```bash
git remote -v
```

Should show:
```
origin  https://github.com/shaik-kabeer/Major_project-.git (fetch)
origin  https://github.com/shaik-kabeer/Major_project-.git (push)
```





