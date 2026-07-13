# FreePWING patches

This directory is reserved for repository-owned patches against the pinned
FreePWING 1.6.1 source archive.

No patch is part of `TASK-B003`: source identity must remain separate from
build compatibility changes. `TASK-B004` proved that the unmodified source
builds and its modules load with the pinned Perl 5.36 runtime, so this
directory intentionally has no patch file. Any future patch must be justified
by a recorded failure, have a deterministic lexical order, document why the
change is required, and apply from the extracted source root with `patch -p1`.
