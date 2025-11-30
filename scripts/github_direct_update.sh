#!/bin/bash
# Sahool Project - Direct GitHub Update Script
# This script updates the GitHub repository directly without workflow restrictions

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

echo ""
echo "🚀 Sahool Project - Direct GitHub Update"
echo "========================================"
echo ""

# التحقق من GitHub CLI
if ! command -v gh &> /dev/null; then
    error "GitHub CLI not installed. Please install it first."
    exit 1
fi

# التحقق من المصادقة
if ! gh auth status &> /dev/null; then
    error "Not authenticated with GitHub CLI"
    info "Run: gh auth login"
    exit 1
fi

log "GitHub CLI authenticated"

# التحقق من المجلد
if [ ! -d ".git" ]; then
    error "Not a git repository"
    exit 1
fi

REPO_NAME="sahool-project"
OWNER="kafaat"

info "Repository: $OWNER/$REPO_NAME"

# فحص الملفات غير المتتبعة
if [ -n "$(git status --porcelain)" ]; then
    info "Found uncommitted changes"
    git status --short
    echo ""
    
    # إضافة الملفات
    git add -A
    
    # عرض التغييرات
    echo ""
    info "Changes to be committed:"
    git status --short
    echo ""
    
    # إنشاء commit
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    git commit -m "📝 Update project files - $TIMESTAMP

- Sync latest changes
- Update documentation
- Fix configurations
- Add missing files"
    
    log "Commit created successfully"
else
    warn "No changes to commit"
fi

# رفع التغييرات
info "Pushing to GitHub..."

if git push origin master; then
    log "✅ Successfully pushed to GitHub!"
    echo ""
    info "Repository URL: https://github.com/$OWNER/$REPO_NAME"
    info "Latest commit: $(git rev-parse --short HEAD)"
else
    error "Failed to push to GitHub"
    exit 1
fi

# عرض آخر 3 commits
echo ""
info "Recent commits:"
git log --oneline -3

echo ""
log "✨ Update completed successfully!"
