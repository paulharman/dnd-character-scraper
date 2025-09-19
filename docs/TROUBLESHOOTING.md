# Troubleshooting Guide

## Common Issues and Solutions

### Parser Issues

#### "Parser: Error processing character"
**Symptoms**: Parser fails with generic error message

**Solutions**:
1. **Check character data**: Run scraper first to ensure fresh data exists
   ```bash
   python scraper/enhanced_dnd_scraper.py YOUR_CHARACTER_ID
   ```

2. **Verify character ID**: Ensure the character ID is correct and accessible
3. **Check permissions**: Ensure character is public or you have proper session cookies

#### "Module not found" errors
**Symptoms**: Import errors when running scripts

**Solutions**:
1. **Check Python path**: Ensure you're running from the project root directory
2. **Verify installation**: Make sure all requirements are installed
   ```bash
   pip install -r requirements.txt
   ```

### Scraper Issues

#### Rate Limit Errors
**Symptoms**: "Too many requests" or 429 errors

**Solutions**:
1. **Wait for rate limit**: The 30-second delay is automatically enforced
2. **Check configuration**: Verify `delay_between_requests: 30` in `config/scraper.yaml`
3. **Don't modify delays**: The 30-second delay is required by D&D Beyond's API

#### Character Access Errors
**Symptoms**: "Character is private" or 403 errors

**Solutions**:
1. **Make character public**: Set character to public in D&D Beyond
2. **Use session cookie**: Add your D&D Beyond session cookie for private characters
3. **Verify character exists**: Check the character ID is correct

### Discord Issues

#### Webhook Not Working
**Symptoms**: No Discord notifications despite changes

**Solutions**:
1. **Test webhook URL**: Use Discord's webhook testing feature
2. **Check environment variables**: Ensure `DISCORD_WEBHOOK_URL` is set correctly
3. **Verify configuration**: Check `config/discord.yaml` settings
   ```bash
   python discord/discord_monitor.py --validate-config
   ```

#### Too Many/Too Few Notifications
**Symptoms**: Spam notifications or missing important changes

**Solutions**:
1. **Filter change types**: Edit the `change_types` list in `config/discord.yaml`
2. **Adjust priority levels**: Set `min_priority` to filter by importance
3. **Check retention**: Old change logs may cause false positives

### Configuration Issues

#### "Configuration validation failed"
**Symptoms**: Errors loading configuration files

**Solutions**:
1. **Check YAML syntax**: Ensure proper indentation and syntax
2. **Validate configuration**: Run the validation tools
   ```bash
   python scripts/security_audit.py
   ```
3. **Reset to defaults**: Compare with example configurations

### File and Directory Issues

#### "Permission denied" errors
**Symptoms**: Cannot write to directories or files

**Solutions**:
1. **Check directory permissions**: Ensure write access to `character_data/`
2. **Create missing directories**: The system should auto-create, but manual creation may help
3. **File locks**: Close any applications that might have files open

### Performance Issues

#### Slow Processing
**Symptoms**: Scripts take a long time to complete

**Solutions**:
1. **Check disk space**: Ensure adequate free space (character data can be large)
2. **Large character data**: Consider enabling retention policies to limit file accumulation
3. **Network issues**: Slow API responses from D&D Beyond

## Getting Help

### Debug Mode
Enable debug mode for detailed error information:
```yaml
# config/main.yaml
debug: true
logging:
  level: "DEBUG"
```

### Log Analysis
Check logs for detailed error information:
- Console output for immediate errors
- `custom_logs/error_log.json` for persistent error tracking

### Security Audit
Run comprehensive security and configuration audit:
```bash
python scripts/security_audit.py
```

### Validation Tools
Test your setup:
```bash
# Quick validation
python validate.py

# Discord configuration check  
python discord/discord_monitor.py --validate-config

# Test webhook connectivity
python discord/discord_monitor.py --validate-webhook
```

## Reporting Issues

When reporting issues, please include:
1. **Error messages**: Complete error output
2. **Configuration**: Relevant configuration files (remove sensitive data)
3. **Environment**: Operating system, Python version
4. **Steps to reproduce**: What you were trying to do when the error occurred
5. **Character data**: If willing, sample character data that causes issues

## Recovery Steps

### Reset Configuration
1. **Backup current config**: Copy `config/` directory
2. **Restore examples**: Copy from `.example` files
3. **Reconfigure**: Set up your specific settings again

### Clean Character Data
If character data seems corrupted:
1. **Backup important data**: Copy `character_data/parser/` (your generated sheets)
2. **Clear cache**: Delete files in `character_data/scraper/` and `character_data/discord/`
3. **Re-scrape**: Run scraper again to get fresh data

### Database Reset
If change tracking seems broken:
1. **Backup change logs**: Copy `character_data/change_logs/`
2. **Clear discord data**: Delete files in `character_data/discord/`
3. **Fresh start**: Run the full pipeline to rebuild change tracking