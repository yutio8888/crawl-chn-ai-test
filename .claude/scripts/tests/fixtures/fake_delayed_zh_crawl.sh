#!/bin/sh

# Reproduce a cold CI startup that exceeds the former three-second probe.
sleep 3.2
printf '\033[2J生命: 10/10\r\n魔力: 5/5\r\n魔法飞弹\r\n'
sleep 1
