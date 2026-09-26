#!/usr/bin/env bash
# Push the profile README using a GitHub token you enter locally.
#
# The token is read with echo off and passed to git via a temporary askpass
# helper, so it is never written to .git/config, never appears in the process
# arguments, and never appears in this chat.
#
# Required token scopes (classic PAT):
#   public_repo  - push to this public repository
#   workflow     - REQUIRED because this commit edits .github/workflows/*
set -euo pipefail

cd "$(dirname "$0")"

echo "This pushes commit: $(git log --oneline -1)"
echo
printf 'Paste your GitHub token (input stays hidden): '
TOKEN=""
IFS= read -rsp TOKEN || true
echo
echo

if [[ -z "${TOKEN:-}" ]]; then
  echo "No token entered. Nothing was changed."
  exit 1
fi

ASKPASS="$(mktemp)"
cat > "$ASKPASS" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  *sername*) printf '%s\n' "kulraj025" ;;
  *)         printf '%s\n' "$GIT_PROFILE_TOKEN" ;;
esac
EOF
chmod +x "$ASKPASS"
trap 'rm -f "$ASKPASS"; unset GIT_PROFILE_TOKEN TOKEN' EXIT

export GIT_PROFILE_TOKEN="$TOKEN"
export GIT_ASKPASS="$ASKPASS"
export GIT_TERMINAL_PROMPT=0

if git push origin main; then
  echo
  echo "PUSH OK"
  echo "Watch the workflow here: https://github.com/kulraj025/kulraj025/actions"
  echo "View your profile:  https://github.com/kulraj025"
else
  echo
  echo "PUSH FAILED — read the error above:"
  echo "  '403 / workflow scope'  -> token is missing the 'workflow' scope"
  echo "  'repository not found'  -> token belongs to a different account"
  echo "  'Bad credentials'       -> token is wrong, expired, or revoked"
fi
