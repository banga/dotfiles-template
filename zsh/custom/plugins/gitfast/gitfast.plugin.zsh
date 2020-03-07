dir=$(dirname $0)
gitfast_dir="$ZSH/plugins/gitfast"
source $dir/../git/git.plugin.zsh
source $gitfast_dir/git-prompt.sh

function git_prompt_info() {
  dirty="$(parse_git_dirty)"
  __git_ps1 "${ZSH_THEME_GIT_PROMPT_PREFIX//\%/%%}%s${dirty//\%/%%}${ZSH_THEME_GIT_PROMPT_SUFFIX//\%/%%}"
}
