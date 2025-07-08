# Git Setup Guide for D&D Character Scraper

This is a beginner's guide to setting up Git and GitHub for the D&D Character Scraper project.

## 1. Install Git

**Windows**: Download from https://git-scm.com/download/windows
**Mac**: `brew install git` or download from git-scm.com
**Linux**: `sudo apt install git` (Ubuntu) or equivalent

## 2. Configure Git (One-time setup)

Open a terminal/command prompt and run:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 3. Create GitHub Account

- Go to https://github.com and sign up
- This is where your code will be stored online

## 4. Initialize Your Project

Open terminal/command prompt and navigate to your project:

```bash
# Navigate to your project directory
cd /mnt/c/Users/alc_u/Documents/DnD/CharacterScraper

# Initialize git
git init

# Create .gitignore file to ignore temporary files
echo "__pycache__/
*.pyc
*.pyo
.env
venv/
.pytest_cache/
coverage.xml
*.log" > .gitignore

# Add your files
git add .
git commit -m "Initial commit - D&D character scraper v5.2.0"
```

## 5. Create GitHub Repository

- Go to https://github.com/new
- Repository name: `dnd-character-scraper` (or whatever you prefer)
- Set to **Private** (recommended for personal tools)
- Don't initialize with README (since you already have files)
- Click "Create repository"

## 6. Connect Local to GitHub

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/dnd-character-scraper.git
git branch -M main
git push -u origin main
```

## 7. Basic Git Workflow (Daily Use)

```bash
# See what changed
git status

# Add changes
git add .

# Commit with a message
git commit -m "Describe what you changed"

# Push to GitHub
git push
```

## 8. For Claude Development

Once your repo is on GitHub:
- Give Claude the repository URL
- Claude can create branches, make changes, and test them
- You can review changes before merging
- All changes are tracked and reversible

## Common Git Commands Reference

```bash
git status          # See what files changed
git add filename    # Stage a specific file
git add .           # Stage all changes
git commit -m "msg" # Save changes with message
git push           # Upload to GitHub
git pull           # Download latest changes
git log --oneline  # See commit history
```

## Troubleshooting

### If you get authentication errors:
- GitHub now requires personal access tokens instead of passwords
- Go to GitHub Settings > Developer settings > Personal access tokens
- Generate a token and use it as your password

### If you're on Windows and get line ending warnings:
```bash
git config --global core.autocrlf true
```

### If you want to see a visual interface:
- GitHub Desktop: https://desktop.github.com/
- VS Code has built-in Git support
- GitKraken (free for personal use)

## Next Steps

1. Complete Git setup above
2. Share repository URL with Claude
3. Claude can help implement the refactor plan with automated testing
4. All changes will be tracked and reversible

## Quick Start Summary

If you just want the bare minimum:

```bash
# One time setup
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# In project folder
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git push -u origin main
```

That's it! You now have version control and can collaborate with Claude on improvements.