# Himal OS - branded shell environment. Build by Samir Puri
[ -n "${BASH_VERSION:-}" ] || return 0

# branded prompt: cyan path on Himal navy, with a hex marker
if [ "$(id -u)" -eq 0 ]; then
    PS1='\[\e[38;5;203m\]\u@\h\[\e[0m\] \[\e[38;5;39m\]\w\[\e[0m\] \[\e[38;5;244m\]#\[\e[0m\] '
else
    PS1='\[\e[38;5;39m\]\u@\h\[\e[0m\] \[\e[38;5;250m\]\w\[\e[0m\] \[\e[38;5;39m\]\xE2\xAC\xA2\[\e[0m\] '
fi

# fastfetch banner on login shells only, if present
if [ -n "${HIMAL_BANNER_SHOWN:-}" ]; then :
elif [ -x /usr/bin/fastfetch ] && [ -t 1 ]; then
    export HIMAL_BANNER_SHOWN=1
    fastfetch 2>/dev/null || true
fi
