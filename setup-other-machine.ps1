# ===================================================================
# D&D Beyond Character Scraper - Setup Script for Second Machine
# ===================================================================
# Run this script on a fresh Windows machine to set up the project.
# Prerequisites: Obsidian vault already synced via Google Drive
#
# Usage: Right-click > Run with PowerShell
#   or:  powershell -ExecutionPolicy Bypass -File setup-other-machine.ps1
# ===================================================================

# Use Continue (PowerShell default) - "Stop" causes native commands that write
# to stderr (git, gh, python) to be treated as terminating errors
$ErrorActionPreference = "Continue"

# --- Configuration ---
$ProjectDir   = "C:\Users\alc_u\Documents\DnD\CharacterScraper - Kiro"
$PrivateRepo  = "https://github.com/paulharman/dnd-character-scraper-private.git"
$PublicRepo   = "https://github.com/paulharman/dnd-character-scraper.git"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " D&D Character Scraper - Machine Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ===================================================================
# 1. Check for Git
# ===================================================================
Write-Host "[1/5] Checking for Git..." -ForegroundColor Yellow
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "  Git not found. Installing via winget..." -ForegroundColor DarkYellow
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        Write-Host "  ERROR: Git install failed. Install manually from https://git-scm.com" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  Git found: $(git --version)" -ForegroundColor Green

# ===================================================================
# 2. Check for Python
# ===================================================================
Write-Host "[2/5] Checking for Python..." -ForegroundColor Yellow

# Determine which Python command works (py launcher is most reliable on Windows)
$pythonCmd = $null

# Helper: test if a python command is real (not the Windows Store alias)
function Test-PythonCommand($cmd) {
    try {
        $result = & $cmd --version 2>&1 | Out-String
        if ($result -match "Python \d") { return $true }
    } catch {}
    return $false
}

# Try py launcher first (comes with official Python installer, avoids Store alias)
if (Get-Command py -ErrorAction SilentlyContinue) {
    if (Test-PythonCommand "py") { $pythonCmd = "py" }
}

# Try python command, but verify it's real (not the Windows Store alias)
if (-not $pythonCmd) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-PythonCommand "python") { $pythonCmd = "python" }
    }
}

if (-not $pythonCmd) {
    Write-Host "  Python not found. Installing via winget..." -ForegroundColor DarkYellow
    winget install --id Python.Python.3.13 -e --source winget --accept-package-agreements --accept-source-agreements
    # Refresh PATH after install
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    # After install, py launcher should be available
    foreach ($cmd in @("py", "python")) {
        if (Test-PythonCommand $cmd) {
            $pythonCmd = $cmd
            break
        }
    }
    if (-not $pythonCmd) {
        Write-Host "  ERROR: Python install succeeded but command not found." -ForegroundColor Red
        Write-Host "  Close this window, open a new terminal, and run the script again." -ForegroundColor Red
        Read-Host "Press Enter to close"
        exit 1
    }
}
$pyVersion = (& $pythonCmd --version 2>&1 | Out-String).Trim()
Write-Host "  Python found: $pyVersion (using '$pythonCmd')" -ForegroundColor Green

# ===================================================================
# 3. Check for GitHub CLI and authenticate
# ===================================================================
Write-Host "[3/5] Checking for GitHub CLI..." -ForegroundColor Yellow
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    # Check common install location
    $ghPath = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path $ghPath) {
        $env:Path += ";C:\Program Files\GitHub CLI"
        $gh = Get-Command gh -ErrorAction SilentlyContinue
    }
}
if (-not $gh) {
    Write-Host "  GitHub CLI not found. Installing via winget..." -ForegroundColor DarkYellow
    winget install --id GitHub.cli -e --source winget --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $gh) {
        Write-Host "  WARNING: GitHub CLI install may need a terminal restart." -ForegroundColor DarkYellow
        Write-Host "  You can install manually from https://cli.github.com" -ForegroundColor DarkYellow
    }
}
$ghAuthed = $false
if ($gh) {
    $ghVer = (gh --version 2>&1 | Out-String).Trim().Split("`n")[0]
    Write-Host "  GitHub CLI found: $ghVer" -ForegroundColor Green
    # Check auth status (gh writes to stderr when not logged in)
    try {
        $null = gh auth status 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) { $ghAuthed = $true }
    } catch {}
    if (-not $ghAuthed) {
        Write-Host "  Not authenticated with GitHub." -ForegroundColor DarkYellow
        Write-Host "  After this script finishes, run:" -ForegroundColor DarkYellow
        Write-Host "    gh auth login" -ForegroundColor White
        Write-Host "  Then run this script again to clone the repo." -ForegroundColor DarkYellow
    } else {
        Write-Host "  GitHub CLI authenticated." -ForegroundColor Green
    }
}

# ===================================================================
# 4. Clone the private repo
# ===================================================================
Write-Host "[4/5] Setting up project repository..." -ForegroundColor Yellow

# Ensure parent directory exists
$parentDir = Split-Path $ProjectDir -Parent
if (-not (Test-Path $parentDir)) {
    Write-Host "  Creating directory: $parentDir" -ForegroundColor DarkYellow
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
}

if (Test-Path (Join-Path $ProjectDir ".git")) {
    Write-Host "  Project already cloned at $ProjectDir" -ForegroundColor Green
    Write-Host "  Pulling latest changes..." -ForegroundColor DarkYellow
    Push-Location $ProjectDir
    git fetch --all
    git checkout full
    git pull private full
    Pop-Location
} elseif (-not $ghAuthed) {
    Write-Host "  SKIPPED: Cannot clone private repo without GitHub authentication." -ForegroundColor DarkYellow
    Write-Host "  After authenticating (gh auth login), run this script again." -ForegroundColor DarkYellow
} else {
    Write-Host "  Cloning from private repo..." -ForegroundColor DarkYellow
    git clone -b full $PrivateRepo $ProjectDir
    Push-Location $ProjectDir
    # Add the public remote as 'origin' (clone sets private as origin, so rename)
    git remote rename origin private
    git remote add origin $PublicRepo
    Pop-Location
    Write-Host "  Repository cloned and remotes configured." -ForegroundColor Green
}

# ===================================================================
# 5. Install Python dependencies and create .env
# ===================================================================
Write-Host "[5/5] Installing Python dependencies..." -ForegroundColor Yellow
$reqFile = Join-Path $ProjectDir "requirements.txt"
if (Test-Path $reqFile) {
    & $pythonCmd -m pip install --upgrade pip 2>&1 | Out-Null
    & $pythonCmd -m pip install -r $reqFile
    Write-Host "  Dependencies installed." -ForegroundColor Green
} else {
    Write-Host "  WARNING: requirements.txt not found (repo not cloned yet?)" -ForegroundColor DarkYellow
}

# Create .env template if missing
$envFile = Join-Path $ProjectDir ".env"
if (Test-Path $envFile) {
    Write-Host "  .env file already exists." -ForegroundColor Green
} elseif (Test-Path $ProjectDir) {
    $envContent = @"
# D&D Beyond Character Scraper - Environment Variables
# Fill in your values below

# Discord webhook URL for character change notifications
# Get from: Discord Server Settings > Integrations > Webhooks > Copy Webhook URL
DISCORD_WEBHOOK_URL=

# D&D Beyond cobalt session token for accessing private characters
# Get from: Browser DevTools > Network tab > any request to character-service.dndbeyond.com
#   > Cookie header > cobalt-session value
DNDBEYOND_COBALT_TOKEN=
"@
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Host "  .env template created." -ForegroundColor Green
    Write-Host "  IMPORTANT: Edit this file and fill in your values!" -ForegroundColor Red
}

# ===================================================================
# Summary
# ===================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
if (-not $ghAuthed) {
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Run: gh auth login" -ForegroundColor White
    Write-Host "  2. Run this script again to clone the repo" -ForegroundColor White
} else {
    Write-Host "Remaining manual step:" -ForegroundColor Yellow
    Write-Host "  Edit $envFile" -ForegroundColor White
    Write-Host "     - Add your DISCORD_WEBHOOK_URL" -ForegroundColor White
    Write-Host "     - Add your DNDBEYOND_COBALT_TOKEN" -ForegroundColor White
}
Write-Host ""
Write-Host "Project: $ProjectDir" -ForegroundColor DarkGray
Write-Host ""

# Keep window open
Read-Host "Press Enter to close"
