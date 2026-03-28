#!/bin/bash
# Simplified version release script (X.Y format)

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Datakart Release Tool ===${NC}\n"

# 1. Branch check (Recommend main/master)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
  echo -e "${YELLOW}Warning: Current branch is '$CURRENT_BRANCH'. Releases are usually done from 'main'.${NC}"
  read -p "Continue anyway? (y/n): " branch_confirm
  if [[ "$branch_confirm" != "y" ]]; then
    exit 1
  fi
fi

# 2. Get current version (Supports X.Y)
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1")
CURRENT_VERSION=${LATEST_TAG#v}

# Split version (Major.Minor) - Ignores third digit if exists
IFS='.' read -r MAJOR MINOR REST <<< "$CURRENT_VERSION"
[[ -z "$MINOR" ]] && MINOR=0

echo -e "Current Version: ${YELLOW}${MAJOR}.${MINOR}${NC}"
echo -e "Select release type:"
echo "1) Minor (${MAJOR}.$((MINOR+1))) - Features or Bug fixes"
echo "2) Major ($((MAJOR+1)).0) - Breaking changes"
read -p "Selection (1-2): " choice

case $choice in
  1)
    NEW_VERSION="${MAJOR}.$((MINOR+1))"
    TYPE="Minor"
    ;;
  2)
    NEW_VERSION="$((MAJOR+1)).0"
    TYPE="Major"
    ;;
  *)
    echo -e "${RED}Invalid selection.${NC}"
    exit 1
    ;;
esac

echo -e "\nNew ${TYPE} Release: ${GREEN}v${NEW_VERSION}${NC} (from v${MAJOR}.${MINOR})"
read -p "Proceed? (y/n): " confirm

if [[ "$confirm" != "y" ]]; then
  echo "Cancelled."
  exit 1
fi

# 3. Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
  echo -e "${RED}Error: You have uncommitted changes. Please commit or stash them first.${NC}"
  exit 1
fi

# 4. Create tag
TAG="v${NEW_VERSION}"
git tag -a "$TAG" -m "Release $NEW_VERSION"

echo -e "${GREEN}Success: Tag ${TAG} created.${NC}"
echo ""

# 5. Optional remote push
read -p "Push the tag to origin now? (y/n): " push_confirm
if [[ "$push_confirm" == "y" ]]; then
  git push origin "$TAG"
  echo -e "${GREEN}Remote push completed!${NC}"
else
  echo -e "\n${YELLOW}Run the following command to push manually:${NC}"
  echo "git push origin $TAG"
fi

echo ""
echo -e "${YELLOW}GitHub Actions will automatically:${NC}"
echo "1. Run tests"
echo "2. Build and publish to PyPI (via OIDC)"
echo "3. Create a GitHub Release with artifacts"
