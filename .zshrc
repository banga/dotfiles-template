#!/bin/sh

source ~/.shrc

# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="clean"

# Annoying beeps
setopt NO_BEEP

# Remove duplicates from history
setopt HIST_IGNORE_ALL_DUPS

# Alt-back and forward to skip over words
bindkey '[D' backward-word
bindkey '[C' forward-word

# Disable smart URL quoting
DISABLE_MAGIC_FUNCTIONS=true

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
plugins=(gitfast yarn zsh-autosuggestions zsh-syntax-highlighting)

DISABLE_UPDATE_PROMPT=true

source $ZSH/oh-my-zsh.sh
