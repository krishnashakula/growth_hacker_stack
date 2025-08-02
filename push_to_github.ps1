# ========================================
# GitHub Push Helper Script
# ========================================

Write-Host "🚀 GitHub Push Helper" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

Write-Host ""
Write-Host "📋 Steps to push to GitHub:" -ForegroundColor Yellow
Write-Host ""

Write-Host "1️⃣ Create GitHub Repository:" -ForegroundColor Cyan
Write-Host "   - Go to https://github.com/new"
Write-Host "   - Repository name: growth_hacker_stack"
Write-Host "   - Description: Enterprise-grade LinkedIn automation stack"
Write-Host "   - Make it Public (or Private)"
Write-Host "   - DON'T initialize with README, .gitignore, or license"
Write-Host "   - Click 'Create repository'"
Write-Host ""

Write-Host "2️⃣ Copy the repository URL (it will look like):" -ForegroundColor Cyan
Write-Host "   https://github.com/yourusername/growth_hacker_stack.git"
Write-Host ""

Write-Host "3️⃣ Run these commands:" -ForegroundColor Cyan
Write-Host "   git remote add origin https://github.com/yourusername/growth_hacker_stack.git"
Write-Host "   git push -u origin main"
Write-Host ""

Write-Host "4️⃣ Alternative: Use HTTPS with token" -ForegroundColor Cyan
Write-Host "   git remote add origin https://your-token@github.com/yourusername/growth_hacker_stack.git"
Write-Host ""

Write-Host "🔧 Current Git Status:" -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "📊 Recent Commits:" -ForegroundColor Yellow
git log --oneline -3

Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Green
Write-Host "   - Make sure you're logged into GitHub in your browser"
Write-Host "   - If you get authentication errors, use a Personal Access Token"
Write-Host "   - You can create a token at: https://github.com/settings/tokens"
Write-Host ""

Write-Host "🎯 Ready to push? Follow the steps above!" -ForegroundColor Green 