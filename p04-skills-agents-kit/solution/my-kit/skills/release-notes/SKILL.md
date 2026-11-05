---
name: release-notes
description: Draft release notes between two git refs, for example /release-notes v1.2.0 v1.3.0.
argument-hint: "<from-ref> <to-ref>"
allowed-tools: Bash(git log *), Bash(git diff --stat *)
disable-model-invocation: true
---
Draft release notes for the changes from `$0` to `$1`.

1. Run `git log --no-merges --pretty=format:"%h %s" $0..$1` and `git diff --stat $0..$1`.
2. Group the changes under **Added**, **Changed**, **Fixed** and **Removed**; skip empty groups.
3. Write each item for users, not developers: what they can now do, in one line.
4. End with an **Upgrade notes** section only if something needs action from users.

Do not invent changes that are not in the log.
