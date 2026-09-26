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

# Push HEAD to refs/heads/main explicitly. `git push origin main` pushes the
# local branch called "main", which is not necessarily where this work is: the
# checkout is often detached, and the local `main` can be many commits behind
# origin/main. That combination fails as "non-fast-forward" while looking like
# a race with the graphics bot, which sends you rebasing onto a branch you were
# never on. Naming the destination ref removes the ambiguity.
if [[ -z "$(git branch --show-current)" ]]; then
  echo "note: HEAD is detached; pushing it straight to refs/heads/main."
fi
echo

# `read -rsp TOKEN` is a trap: bash parses it as `-r -s -p TOKEN`, so the prompt
# becomes the string "TOKEN" and the value lands in $REPLY. $TOKEN is then always
# empty and the script reports "No token entered" for a token that was typed
# correctly. The prompt and the variable name have to be separate arguments.
TOKEN=""
if ! IFS= read -rsp "Paste your GitHub token (input stays hidden): " TOKEN; then
  echo
  echo "Could not read the token. Nothing was changed."
  exit 1
fi
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

if git push origin HEAD:refs/heads/main; then
  echo
  echo "PUSH OK"
  echo "Watch the workflow here: https://github.com/kulraj025/kulraj025/actions"
  echo "View your profile:  https://github.com/kulraj025"
else
  echo
  echo "PUSH FAILED — read the error above:"
  echo "  'non-fast-forward'      -> origin/main moved. Run:"
  echo "                             git fetch origin main && git rebase origin/main"
  echo "                             then run this script again."
  echo "  '403 / workflow scope'  -> token is missing the 'workflow' scope"
  echo "  'repository not found'  -> token belongs to a different account"
  echo "  'Bad credentials'       -> token is wrong, expired, or revoked"
fi
