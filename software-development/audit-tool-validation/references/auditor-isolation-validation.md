# Independent auditor isolation validation

Use when validating a reviewer agent or a bootstrap that claims restricted
access. This is an acceptance checklist, not a tested launcher template.

## 1. Separate identity, execution and security boundaries

- Establish whether the request needs a reusable review prompt, an ephemeral
  delegated conversation, a persistent Hermes home, or an independently
  supervised OS process. Do not substitute a skill for a requested persistent
  auditor; a skill instructs the caller and has no independent lifecycle.
- Resolve the installed profile-selection semantics before fixing paths.
  Distinguish the pre-selection home from a selected named profile's effective
  home. Alternatively choose a standalone home without profile selection and
  keep every launcher/config/memory path consistent with that decision.
- Treat a separate Hermes home as state separation, not an OS sandbox. Likewise,
  a different working directory and the absence of a terminal tool do not
  restrict the process's filesystem or network permissions.
- Inspect the actual exposed tool schemas and internal execution paths. A file
  toolset can write and patch; document extraction or linting can spawn helper
  processes even when no terminal tool is exposed to the model.
- Give a persistent auditor its own minimal identity, memory and evidence
  history. Send original requirements, immutable artifact identifiers, known
  defects and raw test evidence; do not send only the author's favorable summary.
  Require proof for criticism and do not reward disagreement for its own sake.

## 2. Define the allowed data flows first

Use read-only reviewed inputs and a distinct writable report location. Keep
original production files and credentials outside the auditor's OS permissions.
Do not open traversal rights on an otherwise private parent directory just to
reach a convenient child path. Give the runtime a non-auditor owner and no
write bits for group/other; verify ACLs as well as mode bits.

For an independently installed runtime, pin the actual source revision and
locked dependencies. Do not relocate an existing venv blindly: inspect shebangs,
resolved symlinks, `pyvenv.cfg`, executable import hooks, `sys.path`, RPATH/RUNPATH,
and resolved shared libraries. With uv project synchronization, set
`UV_PROJECT_ENVIRONMENT` explicitly and pass the intended interpreter with
`--python`; do not assume `VIRTUAL_ENV` selects the project environment.

Do not remove Python site initialization merely to simplify a launcher; venv
site-packages and installed package hooks may be required. Run functional
smoke-tests from the target unprivileged UID after installation is authorized.

## 3. Validate the bootstrap independently of the model

1. Check the installed privilege tool's supported options. Use an explicit
   environment allowlist, fixed executable/home selection, and a restricted CLI
   contract rather than forwarding arbitrary profile/config arguments.
2. Verify real/effective/saved UID and GID, supplementary groups, all capability
   sets, and `NoNewPrivs` on the running process. A passwd entry with `nologin`
   does not prevent direct execution under that UID; `--init-groups` loads all
   configured memberships and does not mean only one group.
3. Sanitize standard streams independently of FD 3+. Already-open stdin,
   stdout or stderr can carry access to a protected file after a UID change.
   `env -i`, privilege dropping and `exec` do not automatically close inheritable
   descriptors.
4. Close all unwanted inherited descriptors, including high-numbered FDs and
   FDs above a subsequently lowered soft `RLIMIT_NOFILE`. Do not stop at 1023
   or infer the underlying syscall merely from `os.closerange` being present.
5. Account for `/proc/self/fd` enumeration opening a temporary descriptor of its
   own. Verify candidate descriptors with `fstat` after enumeration; do not
   interpret a vanished enumeration FD as a persistent leak.
6. Use three distinct synthetic, root-protected canary files for FD 0/1/2 and
   separate sentinel FDs above 2, including one above 1023. Never redirect test
   output to a real secret: shell `>` can truncate it before the launcher runs.
7. Use the same sanitization path in probe and real startup. Hold the probe at a
   readiness handshake or an observed stop state while the parent examines
   `/proc/PID/fd` and `/proc/PID/status`. Inspect canary device/inode identity as
   well as links. Do not rely only on sleep or the child's self-reported log.
8. Test absence of inherited canaries, not an exact count of three descriptors
   in a running application: its own sockets, databases and logs are legitimate.
   Use OS-level access probes for protected reads and denied writes, rather than
   a prompt asking the model whether it can access a file.

## 4. Make logging a controlled exception

Validate the parent path before opening a log. Open through checked directory
file descriptors with no-follow flags, then verify the resulting file with
`fstat` (owner, group, mode, regular-file type and link count). A pathname check
followed by ordinary shell redirection is not a race-free open, and a check
performed after redirection is too late.

Declare append-only log descriptors as an explicit permitted output channel if
opened by a privileged launcher and handed to the auditor. Choose a rotation
strategy the writer actually supports. Do not call `copytruncate` lossless or
mandatory: copying and truncating a live log can lose concurrent writes. Test
rotation, reopen behavior and symlink refusal before relying on logs as evidence.

## 5. Admit materials only after review

Until an archive/binary scanner has passed adversarial tests, allow only
individually reviewed artifacts identified by exact hashes. A rule matching no
known token pattern is not proof that a file contains no secrets. Keep unknown,
flagged and unreviewed materials outside the reader's visible input directories.

For a future scanner, test per-file classification, embedded configurations,
metadata/OCR where relevant, nested archives, encrypted or unsupported formats,
Unicode paths, duplicate entries, symlinks/hardlinks, path traversal, entry-count
and expansion limits. Validate archive metadata before extraction and enforce
streaming output/time/resource budgets during extraction; declared sizes alone
cannot stop a decompression bomb. Keep report paths independent of archive member
names. Treat parser errors and unavailable decoders as unknown/refused, never
clean. Do not preserve an untested extraction snippet as a security gate.
