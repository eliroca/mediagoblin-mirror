#!/bin/sh

set -e

aclocal -I m4 --install
autoreconf -fvi

git submodule update --init
