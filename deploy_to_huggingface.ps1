# Deploy to Hugging Face Spaces
# Usage: .\deploy_to_huggingface.ps1 -HF_USERNAME "your_username"

param(
    [Parameter(Mandatory=$true)]
    [string]$HF_USERNAME,
    
    [Parameter(Mandatory=$false)]
    [string]$SPACE_NAME = "fraud-detection-system"
)

$HF_URL = "https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
$DEPLOY_DIR = "deployment_hf"

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🚀 Deploying Enterprise Fraud Detection System to Hugging Face Spaces" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Step 1: Create deployment directory
Write-Host "📁 Step 1: Creating deployment package..." -ForegroundColor Yellow

if (Test-Path $DEPLOY_DIR) {
    Write-Host "   ⚠️  Deployment directory exists. Removing..." -ForegroundColor Yellow
    Remove-Item $DEPLOY_DIR -Recurse -Force
}

New-Item -Path $DEPLOY_DIR -ItemType Directory -Force | Out-Null
Write-Host "   ✅ Deployment directory created" -ForegroundColor Green

# Step 2: Copy files
Write-Host ""
Write-Host "📦 Step 2: Copying files..." -ForegroundColor Yellow

# Copy main files
Copy-Item -Path "app.py" -Destination "$DEPLOY_DIR\" -Force
Copy-Item -Path "requirements_hf.txt" -Destination "$DEPLOY_DIR\requirements.txt" -Force
Copy-Item -Path "README_HF.md" -Destination "$DEPLOY_DIR\README.md" -Force

Write-Host "   ✅ Main files copied" -ForegroundColor Green

# Copy source code
if (Test-Path "src") {
    Copy-Item -Path "src" -Destination "$DEPLOY_DIR\" -Recurse -Force
    Write-Host "   ✅ Source code copied" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Source code not found!" -ForegroundColor Red
    exit 1
}

# Copy models
if (Test-Path "models") {
    Copy-Item -Path "models" -Destination "$DEPLOY_DIR\" -Recurse -Force
    Write-Host "   ✅ Models copied" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Models not found! Train the model first." -ForegroundColor Red
    exit 1
}

# Copy scripts (optional)
if (Test-Path "scripts") {
    Copy-Item -Path "scripts" -Destination "$DEPLOY_DIR\" -Recurse -Force
    Write-Host "   ✅ Scripts copied" -ForegroundColor Green
}

# Step 3: Create .gitignore
Write-Host ""
Write-Host "📝 Step 3: Creating .gitignore..." -ForegroundColor Yellow

$gitignore = @"
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
.env
.venv
venv/
*.log
.DS_Store
"@

Set-Content -Path "$DEPLOY_DIR\.gitignore" -Value $gitignore
Write-Host "   ✅ .gitignore created" -ForegroundColor Green

# Step 4: Initialize git
Write-Host ""
Write-Host "🔧 Step 4: Initializing git repository..." -ForegroundColor Yellow

Set-Location $DEPLOY_DIR

git init | Out-Null
git add . | Out-Null
git commit -m "Initial commit: Enterprise Fraud Detection System" | Out-Null

Write-Host "   ✅ Git repository initialized" -ForegroundColor Green

# Step 5: Add remote and prepare to push
Write-Host ""
Write-Host "🔗 Step 5: Adding Hugging Face remote..." -ForegroundColor Yellow

git remote add origin $HF_URL

Write-Host "   ✅ Remote added: $HF_URL" -ForegroundColor Green

# Step 6: Instructions for pushing
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📋 NEXT STEPS - Manual Push Required" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  Get Hugging Face Access Token:" -ForegroundColor Yellow
Write-Host "   - Go to: https://huggingface.co/settings/tokens" -ForegroundColor White
Write-Host "   - Click 'New token'" -ForegroundColor White
Write-Host "   - Name: 'fraud-detection-deploy'" -ForegroundColor White
Write-Host "   - Type: Write" -ForegroundColor White
Write-Host "   - Click 'Generate' and COPY the token" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣  Create Hugging Face Space (if not exists):" -ForegroundColor Yellow
Write-Host "   - Go to: https://huggingface.co/spaces" -ForegroundColor White
Write-Host "   - Click 'Create new Space'" -ForegroundColor White
Write-Host "   - Space name: $SPACE_NAME" -ForegroundColor White
Write-Host "   - SDK: Gradio" -ForegroundColor White
Write-Host "   - Hardware: CPU (free)" -ForegroundColor White
Write-Host "   - Click 'Create Space'" -ForegroundColor White
Write-Host ""

Write-Host "3️⃣  Push to Hugging Face:" -ForegroundColor Yellow
Write-Host "   Run this command:" -ForegroundColor White
Write-Host ""
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "   When asked for credentials:" -ForegroundColor White
Write-Host "   - Username: $HF_USERNAME" -ForegroundColor White
Write-Host "   - Password: [PASTE YOUR ACCESS TOKEN]" -ForegroundColor White
Write-Host ""

Write-Host "4️⃣  Wait for deployment (2-5 minutes)" -ForegroundColor Yellow
Write-Host "   Your app will be live at:" -ForegroundColor White
Write-Host "   $HF_URL" -ForegroundColor Cyan
Write-Host ""

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ Deployment package ready in: $DEPLOY_DIR\" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "📍 Current directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""
Write-Host "To push now, run: git push -u origin main" -ForegroundColor Cyan
Write-Host ""
