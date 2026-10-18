#!/bin/bash
# Build the pinned SAT solver and proof checkers used by audit.py.
# usage: SAT_TOOLS=/some/dir r310/build_tools.sh
set -e
D="${SAT_TOOLS:?set SAT_TOOLS to a directory}"
mkdir -p "$D" && cd "$D"
fetch() { [ -d "$1" ] || git clone -q "$2" "$1"; git -C "$1" checkout -q "$3"; }
fetch cadical   https://github.com/arminbiere/cadical.git   c60730422e758ef1cebe7aeddf2dda31c996bf04
fetch drat-trim https://github.com/marijnheule/drat-trim.git 2e3b2dc0ecf938addbd779d42877b6ed69d9a985
fetch lrat-trim https://github.com/arminbiere/lrat-trim.git  b30f400f4ee5c32b77ee566a7c006081b521534f
(cd cadical && ./configure >/dev/null && make -j4 >/dev/null)
(cd drat-trim && make >/dev/null)
(cd lrat-trim && ./configure >/dev/null && make >/dev/null)
echo "built in $D"
