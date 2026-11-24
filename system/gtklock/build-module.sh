#!/bin/sh
set -eu
source_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
target=${XDG_DATA_HOME:-"$HOME/.local/share"}/paperbit/gtklock
mkdir -p "$target"
temporary=$(mktemp "$target/.patterns.XXXXXX")
trap 'test ! -e "$temporary" || unlink "$temporary"' EXIT

# pkg-config emits individual compiler flags.
# shellcheck disable=SC2046
cc -std=c11 -Wall -Wextra -O2 -fPIC -shared -Wl,-z,defs \
  $(pkg-config --cflags gtk+-3.0 gmodule-2.0) \
  "$source_dir/paperbit-patterns.c" \
  $(pkg-config --libs gtk+-3.0 gmodule-2.0) -lm -o "$temporary"
mv -f "$temporary" "$target/paperbit-patterns.so"
