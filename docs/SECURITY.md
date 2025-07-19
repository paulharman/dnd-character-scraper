# Security Guide

This document provides guidance on securely configuring the D&D Beyond Character Scraper, particularly for Discord integration.

## 🔒 Security Best Practices

### 1. Use Environment Variables for Sensitive Data

**Never commit sensitive data to version control.** Instead, use environment variables:

```bash
# Set environment variables (Linux/Mac)
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
export DND_SESSION_COOKIE="your-session-cookie"

# Set environment variables (Windows)
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
set DND_SESSION_COOKIE=your-session-cookie
```

### 2. Configuration File Security

#### Recommended: Use Environment Variables in Config
```yaml
# config/discord.yaml (SECURE)
webhook_url: "${DISCORD_WEBHOOK_URL}"
character_id: 12345  # Character IDs are public identifiers, not sensitive
session_cookie: "${DND_SESSION_COOKIE}"
```

#### Not Recommended: Hardcoded Values
```yaml
# config/discord.yaml (INSECURE - DON'T DO THIS)
webhook_url: "https://discord.com/api/webhooks/123/abc"  # ❌ Exposed in version control
character_id: 12345  # ✅ This is fine - character IDs are public
session_cookie: "hardcoded-cookie"  # ❌ Security risk
```

### 3. File Permissions

Restrict access to configuration files:

```bash
# Linux/Mac - Make config files readable only by owner
chmod 600 config/discord.yaml
chmod 600 .env

# Windows - Use file properties to restrict access
# Right-click → Properties → Security → Advanced
```

### 4. .env File Usage

Create a `.env` file in the project root (automatically ignored by git):

```bash
# .env file
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
DND_SESSION_COOKIE=your-session-cookie-here
LOG_LEVEL=INFO
```

## 🛡️ Security Validation Tools

The project includes built-in security validation tools:

### Security Audit
```bash
python discord/discord_monitor.py --security-check
```
This scans your entire project for:
- Hardcoded webhook URLs
- Exposed session cookies
- Insecure file permissions
- Sensitive data in version control

### Configuration Validation
```bash
python discord/discord_monitor.py --validate-config
```
This validates your configuration for:
- Required fields
- Security warnings
- Best practice recommendations

### Webhook Validation
```bash
python discord/discord_monitor.py --validate-webhook
```
This tests your webhook without exposing sensitive data.

## 🚨 Common Security Issues

### Issue 1: Hardcoded Webhook URLs
**Problem:** Webhook URLs committed to git
**Solution:** Use environment variables
**Detection:** Security audit will flag these

### Issue 2: World-Readable Config Files
**Problem:** Config files readable by all users
**Solution:** `chmod 600 config/discord.yaml`
**Detection:** Security audit checks file permissions

### Issue 3: Session Cookies in Config
**Problem:** D&D Beyond session cookies in config files
**Solution:** Use `DND_SESSION_COOKIE` environment variable
**Detection:** Configuration validator warns about this

## 🔧 Secure Setup Process

### Step 1: Copy Template
```bash
cp config/discord.yaml.template config/discord.yaml
cp .env.example .env
```

### Step 2: Configure Environment Variables
Edit `.env` file with your actual values:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ACTUAL_WEBHOOK_ID/YOUR_ACTUAL_TOKEN
DND_SESSION_COOKIE=YOUR_ACTUAL_SESSION_COOKIE
```

### Step 3: Secure File Permissions
```bash
chmod 600 .env
chmod 600 config/discord.yaml
```

### Step 4: Validate Security
```bash
python discord/discord_monitor.py --security-check
```

### Step 5: Test Configuration
```bash
python discord/discord_monitor.py --validate-config
python discord/discord_monitor.py --validate-webhook
```

## 📋 Security Checklist

- [ ] No hardcoded webhook URLs in config files
- [ ] No hardcoded session cookies in config files  
- [ ] Environment variables configured in `.env` file
- [ ] `.env` file has restricted permissions (600)
- [ ] Config files have restricted permissions (600)
- [ ] `.env` file is in `.gitignore` (already included)
- [ ] Security audit passes without high-severity issues
- [ ] Configuration validation passes
- [ ] Webhook validation succeeds

## 🆘 If You've Already Committed Sensitive Data

If you've accidentally committed webhook URLs or other sensitive data:

### 1. Immediately Regenerate Webhooks
- Go to Discord server settings
- Delete the exposed webhook
- Create a new webhook with a new URL

### 2. Remove from Git History
```bash
# Remove sensitive files from git history (DESTRUCTIVE)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config/discord.yaml' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: This rewrites history)
git push origin --force --all
```

### 3. Update Configuration
- Use environment variables going forward
- Follow the secure setup process above

## 📞 Support

If you need help with security configuration:
1. Run the diagnostic tools first: `--security-check`, `--validate-config`
2. Check this documentation
3. Review the configuration template: `config/discord.yaml.template`
4. Check the example environment file: `.env.example`

Remember: **Security is everyone's responsibility!** 🔐
## 🔒 Git 
Security Protection

### .gitignore Protection

The project includes comprehensive `.gitignore` rules to prevent sensitive files from being committed:

```gitignore
# Security - Sensitive configuration files
.env
.env.local
.env.production
.env.development
config/discord.yaml
discord/discord_config.yml
**/webhook_urls.txt
**/session_cookies.txt
**/*_secrets.*
**/*_private.*

# Additional webhook URL protection patterns
**/discord_webhook_*.txt
**/webhook_*.json
**/webhook_*.yaml
**/webhook_*.yml
**/*webhook*.env
**/*discord*.env
```

### Pre-commit Hook Protection

The project includes an automatic pre-commit hook that scans for sensitive data before allowing commits:

**Features:**
- Detects Discord webhook URLs in staged files
- Identifies session cookies and API keys
- Excludes test files and documentation from checks
- Provides clear guidance on fixing issues
- Cross-platform Python implementation (Windows compatible)

**How it works:**
```bash
# Automatically runs before each commit
git commit -m "Your changes"
# 🔍 Checking for sensitive data before commit...
# ✅ No sensitive data detected. Commit allowed.
```

**If sensitive data is detected:**
```bash
# ❌ SECURITY ALERT: Discord webhook URL detected in staged files!
# 🚫 COMMIT BLOCKED: Sensitive data detected!
# 
# To fix this:
# 1. Remove hardcoded webhook URLs and session cookies from your files
# 2. Use environment variables instead:
#    webhook_url: "${DISCORD_WEBHOOK_URL}"
#    session_cookie: "${DND_SESSION_COOKIE}"
```

### Security Audit Script

Run comprehensive security audits with the included script:

```bash
# Run security audit
python scripts/security_audit.py

# Example output:
# 🔍 Starting security audit...
# 📁 Scanning files for secrets...
# 📋 Checking .gitignore...
# 🔒 Checking file permissions...
# ⚙️ Auditing configurations...
# 
# 🛡️  SECURITY AUDIT REPORT
# ========================================
# 📊 Total Findings: 0
# ✅ No security issues found! Your project looks secure.
```

**Audit Features:**
- Scans all project files for webhook URLs, session cookies, and API keys
- Validates .gitignore security patterns
- Checks file permissions on sensitive files
- Audits configuration files for security issues
- Generates detailed JSON report
- Excludes test files and documentation from security checks

### Manual Security Checks

You can also run manual security checks:

```bash
# Check for webhook URLs in your files (excluding tests)
grep -r "discord.com/api/webhooks" . --exclude-dir=.git --exclude="*test*" --exclude="*.md"

# Check for session cookies
grep -r -i "session.*cookie" . --exclude-dir=.git --exclude="*test*" --exclude="*.md"

# Verify .gitignore is protecting sensitive files
git check-ignore config/discord.yaml  # Should be ignored
git check-ignore .env                 # Should be ignored
```

## 🛡️ Security Best Practices Summary

### ✅ DO:
- Use environment variables for all sensitive data
- Run security audits regularly
- Keep configuration files out of version control
- Use the provided validation tools
- Set restrictive file permissions on sensitive files
- Review the pre-commit hook output

### ❌ DON'T:
- Commit webhook URLs to git
- Store session cookies in configuration files
- Share configuration files containing sensitive data
- Bypass security checks without understanding the risks
- Use `--no-verify` flag unless absolutely necessary

### 🔄 Regular Maintenance:
1. Run `python scripts/security_audit.py` monthly
2. Update environment variables when webhooks change
3. Review file permissions after system updates
4. Validate configurations after changes

This multi-layered security approach ensures your webhook URLs and other sensitive data stay protected from accidental exposure in version control.