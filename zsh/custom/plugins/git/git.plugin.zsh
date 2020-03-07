# Query/use custom command for `git`.
zstyle -s ":vcs_info:git:*:-all-" "command" _omz_git_git_cmd
: ${_omz_git_git_cmd:=git}

#
# Functions
#

# The name of the current branch
# Back-compatibility wrapper for when this function was defined here in
# the plugin, before being pulled in to core lib/git.zsh as git_current_branch()
# to fix the core -> git plugin dependency.
function current_branch() {
  git_current_branch
}
# The list of remotes
function current_repository() {
  if ! $_omz_git_git_cmd rev-parse --is-inside-work-tree &> /dev/null; then
    return
  fi
  echo $($_omz_git_git_cmd remote -v | cut -d':' -f 2)
}
# Pretty log messages
function _git_log_prettily(){
  if ! [ -z $1 ]; then
    git log --pretty=$1
  fi
}
# Warn if the current branch is a WIP
function work_in_progress() {
  if $(git log -n 1 2>/dev/null | grep -q -c "\-\-wip\-\-"); then
    echo "WIP!!"
  fi
}

alias ga='git add'

alias gb='git branch'

alias gc='git commit -v'
alias gcap='git commit -a --amend -C HEAD'
alias gcm='git commit --amend -C HEAD'
alias gco='git checkout'
gf() { git checkout -b "$1" origin/master }
compdef _git gf=git-checkout
alias gcp='git cherry-pick'
alias gd='git diff'
alias gdc='git diff --cached'

gdv() { git diff -w "$@" | view - }
compdef _git gdv=git-diff

alias gl='git log'
alias glg='git log --stat --color'
alias glgp='git log --stat --color -p'
alias glgg='git log --graph --color'
alias glgga='git log --graph --decorate --all'
alias glo='git log --oneline --decorate --color'
alias glog='git log --oneline --decorate --graph'
alias gloga='git log --oneline --decorate --graph --all'
alias glp="_git_log_prettily"
compdef _git glp=git-log

alias grb='git rebase'
alias grba='git rebase --abort'
alias grbc='git rebase --continue'
alias grbi='git rebase -i'
alias grbm='git rebase master'
alias grom='git rebase origin/master'
alias grim='git rebase -i origin/master'
alias grbs='git rebase --skip'
alias grh='git reset --hard'
alias grhh='git reset HEAD --hard'

alias gss='git status -s'
alias gst='git status'

alias gwch='git whatchanged -p --abbrev-commit --pretty=medium'
alias gwip='git add -A; git rm $(git ls-files --deleted) 2> /dev/null; git commit --no-verify -m "--wip-- [skip ci]"'

alias gs='git stash --keep-index --include-untracked'
alias gsa='git stash apply'
alias gsl='git stash list'
alias gsb='git stash branch'
alias gsp='git stash show -p'
alias gsd='git stash drop'