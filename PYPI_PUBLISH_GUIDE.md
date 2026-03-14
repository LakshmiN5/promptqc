# Publishing PromptQC to PyPI - Step-by-Step Guide

## Congratulations on Your First PyPI Package! 🎉

This guide will walk you through publishing PromptQC to PyPI for the first time.

---

## Prerequisites

### 1. Create PyPI Account
1. Go to https://pypi.org/account/register/
2. Fill in:
   - Username (e.g., LakshmiN5)
   - Email
   - Password
3. Verify your email
4. **Enable 2FA** (required for publishing)

### 2. Create API Token (Recommended)
1. Go to https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: "promptqc-upload"
5. Scope: "Entire account" (or specific to promptqc later)
6. **Copy the token** (starts with `pypi-...`)
7. Save it securely - you won't see it again!

---

## Step 1: Install Build Tools

```bash
cd /Users/lakshmi/codeworkspace/ASPIRATIONAL/promptqc

# Install build tools
pip install --upgrade build twine
```

---

## Step 2: Clean Previous Builds (if any)

```bash
# Remove old build artifacts
rm -rf dist/ build/ src/*.egg-info
```

---

## Step 3: Build the Package

```bash
# Build source distribution and wheel
python -m build
```

**Expected output:**
```
Successfully built promptqc-0.2.0.tar.gz and promptqc-0.2.0-py3-none-any.whl
```

**What this creates:**
- `dist/promptqc-0.2.0.tar.gz` - Source distribution
- `dist/promptqc-0.2.0-py3-none-any.whl` - Wheel (binary distribution)

---

## Step 4: Check the Package

```bash
# Verify the package is valid
twine check dist/*
```

**Expected output:**
```
Checking dist/promptqc-0.2.0.tar.gz: PASSED
Checking dist/promptqc-0.2.0-py3-none-any.whl: PASSED
```

If you see errors, fix them before proceeding.

---

## Step 5: Test on TestPyPI (Optional but Recommended)

TestPyPI is a separate instance for testing. It's good practice to test here first.

### 5a. Create TestPyPI Account
1. Go to https://test.pypi.org/account/register/
2. Create account (separate from main PyPI)
3. Create API token (same process as above)

### 5b. Upload to TestPyPI
```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

**You'll be prompted for:**
- Username: `__token__`
- Password: Your TestPyPI API token (paste it)

### 5c. Test Installation from TestPyPI
```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ promptqc

# Test it works
promptqc --version
promptqc quick "You are helpful"

# Clean up
deactivate
rm -rf test_env
```

---

## Step 6: Publish to Real PyPI 🚀

### 6a. Configure Credentials

**Option A: Use API Token (Recommended)**
```bash
# Upload with token
twine upload dist/*
```
- Username: `__token__`
- Password: Your PyPI API token

**Option B: Save Token in Config**
```bash
# Create ~/.pypirc file
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
EOF

chmod 600 ~/.pypirc

# Now you can upload without entering credentials
twine upload dist/*
```

### 6b. Upload!
```bash
twine upload dist/*
```

**Expected output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading promptqc-0.2.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50.0/50.0 kB • 00:01
Uploading promptqc-0.2.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.0/45.0 kB • 00:01

View at:
https://pypi.org/project/promptqc/0.2.0/
```

---

## Step 7: Verify Publication

### 7a. Check PyPI Page
Visit: https://pypi.org/project/promptqc/

You should see:
- Package name and version
- Description from README.md
- Installation instructions
- Links to GitHub

### 7b. Test Installation
```bash
# In a fresh environment
pip install promptqc

# Test it works
promptqc --version
# Should output: promptqc, version 0.2.0

promptqc quick "You are helpful"
# Should run analysis
```

---

## Step 8: Celebrate! 🎉

**You just published your first PyPI package!**

Your package is now available to anyone in the world:
```bash
pip install promptqc
```

---

## Common Issues and Solutions

### Issue: "File already exists"
**Problem:** You're trying to upload a version that already exists.

**Solution:** You can't overwrite PyPI releases. Bump the version:
```bash
# Edit pyproject.toml
version = "0.2.1"  # Increment version

# Rebuild and upload
rm -rf dist/
python -m build
twine upload dist/*
```

### Issue: "Invalid credentials"
**Problem:** Wrong username or token.

**Solution:**
- Username must be `__token__` (not your PyPI username)
- Password is your API token (starts with `pypi-`)
- Make sure you're using PyPI token, not TestPyPI token

### Issue: "Package name already taken"
**Problem:** Someone else has a package called "promptqc".

**Solution:** Check https://pypi.org/project/promptqc/ - if it exists, you'll need to:
1. Choose a different name (e.g., "promptqc-tool", "prompt-qc")
2. Update `name` in pyproject.toml
3. Rebuild and upload

### Issue: "Invalid package metadata"
**Problem:** Something wrong in pyproject.toml.

**Solution:**
```bash
# Check what's wrong
twine check dist/*

# Common fixes:
# - Ensure version follows semver (0.2.0, not 0.2)
# - Check all URLs are valid
# - Ensure description is valid markdown
```

---

## After Publication

### Update GitHub
```bash
# Tag the release
git tag -a v0.2.0 -m "Release v0.2.0 - First PyPI publication"
git push origin v0.2.0

# Create GitHub release
# Go to: https://github.com/LakshmiN5/promptqc/releases/new
# - Tag: v0.2.0
# - Title: "v0.2.0 - First PyPI Release"
# - Description: Copy from CHANGELOG.md
```

### Monitor
- PyPI downloads: https://pypistats.org/packages/promptqc
- GitHub stars: https://github.com/LakshmiN5/promptqc/stargazers
- Issues: https://github.com/LakshmiN5/promptqc/issues

---

## Publishing Updates (Future Versions)

When you want to publish v0.2.1, v0.3.0, etc.:

```bash
# 1. Update version in pyproject.toml
version = "0.3.0"

# 2. Update CHANGELOG.md with changes

# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.3.0"
git push

# 4. Build and upload
rm -rf dist/
python -m build
twine check dist/*
twine upload dist/*

# 5. Tag release
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0
```

---

## Documentation That's "Too Much"

You asked what's too much. Here's my take:

**Keep (Essential):**
- README.md - Main documentation
- LICENSE - Required
- CHANGELOG.md - Version history
- CONTRIBUTING.md - How to contribute

**Optional (Good to Have):**
- test_suite/README.md - Explains test structure
- test_suite/TEST_OBSERVATIONS.md - Test results

**Remove or Move to Wiki (Too Much for Repo):**
- EVALUATION.md - Move to GitHub Wiki or blog post
- PUBLISH_CHECKLIST.md - Delete after publishing
- PYPI_PUBLISH_GUIDE.md - Delete after publishing (or keep in docs/)

**My Recommendation:**
After publishing, clean up:
```bash
# Move to docs/ folder
mkdir -p docs
mv EVALUATION.md docs/
mv PUBLISH_CHECKLIST.md docs/
mv PYPI_PUBLISH_GUIDE.md docs/

# Or delete them
rm EVALUATION.md PUBLISH_CHECKLIST.md PYPI_PUBLISH_GUIDE.md
```

---

## Quick Reference Card

```bash
# Complete publishing workflow
cd /Users/lakshmi/codeworkspace/ASPIRATIONAL/promptqc

# Clean and build
rm -rf dist/ build/ src/*.egg-info
python -m build

# Check
twine check dist/*

# Upload
twine upload dist/*
# Username: __token__
# Password: pypi-YOUR-TOKEN-HERE

# Verify
pip install promptqc
promptqc --version

# Done! 🎉
```

---

**Good luck with your first PyPI publication!** 🚀

If you run into issues, check:
1. PyPI status: https://status.python.org/
2. Twine docs: https://twine.readthedocs.io/
3. Packaging guide: https://packaging.python.org/