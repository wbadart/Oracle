#!/usr/bin/zsh

handle(){
    exit 0
}

trap handle SIGINT SIGKILL SIGTERM

sleep 5

exit 1
