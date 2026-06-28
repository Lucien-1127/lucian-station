---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

This skill is separate from the Hermes Email gateway adapter. The gateway
adapter lets people email the agent and uses Hermes' built-in IMAP/SMTP
adapter; this skill lets the agent operate a mailbox from terminal tools and
requires the external `himalaya` CLI.

## References

- `references/headless-password-storage.md` (practical password storage for headless/SSH environments)
- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)
- `references/inbox-scanning.md` (proactive triage for AI/professional content)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input is the recommended approach. **Always write the email to a temp file first, then pipe with `<` AND explicitly set HOME**: `HOME=/home/<user> himalaya template send < /tmp/email.txt`. Even the `<` pipe can fail with `Could not determine home directory` in Hermes subprocess environments — the HOME env var is the definitive fix. Write the email body to /tmp first so you can inspect it before sending. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

⚠️ HIMALAYA REQUIRES EXPLICIT `and` BETWEEN CONDITIONS. Space-separated terms (`from foo subject bar`) will fail with a parse error.

```bash
# Correct — use `and` between conditions
himalaya envelope list from googlecloud and subject gemini

# Single condition — no `and` needed
himalaya envelope list subject newsletter
himalaya envelope list from "someone@example.com"

# Operators: not / and / or
himalaya envelope list from github and not subject spam
```

📌 **Note on flags:** `--page`, `--page-size` are options that go BEFORE the query, not inside it. They cannot be combined with a search query in the same flag string — use them separately:
```bash
himalaya envelope list --page 1 --page-size 20
# (listing, no search filter)

# Search + pagination works as positional + options:
himalaya envelope list --page 1 --page-size 20 from github and subject release
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — write to a temp file first, then pipe with `<`:

```bash
cat << 'EOF' > /tmp/email.txt
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
himalaya template send < /tmp/email.txt
```

The file-pipe approach is preferred over direct heredoc piping, which can trigger `Could not determine home directory` errors in certain Hermes subprocess environments. Both work, but `<` redirection is more reliable cross-platform.

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
himalaya message move "Archive" 42
# Syntax: himalaya message move <TARGET> <ID>...   (TARGET first, then IDs)
himalaya message move "Archive" 42 43 44   # batch move
```

Copy to folder:

```bash
himalaya message copy "Important" 42
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account:

```bash
himalaya --account work envelope list
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Troubleshooting

### Gmail App Password expired (Invalid credentials / AUTHENTICATIONFAILED)

Gmail App Passwords can expire or get revoked. Symptoms:

```
Error: cannot authenticate to IMAP server using LOGIN mechanism
unexpected NO response: Invalid credentials (Failure)
```

Or from raw SMTP test:
```
535 5.7.8 Username and Password not accepted
```

**Fix**: Generate a new App Password at https://myaccount.google.com/apppasswords and update the password file.

**Detection**: Use Python's smtplib to isolate SMTP auth from IMAP:

```python
import smtplib, ssl
with smtplib.SMTP('smtp.gmail.com', 587) as s:
    s.starttls(context=ssl.create_default_context())
    pw = open('~/.hermes/scripts/gmail-pass.txt').read().strip()
    s.login('hsieh89t@gmail.com', pw)
    print('SMTP OK')
```

If SMTP passes but himalaya fails, the issue is IMAP-specific (less common).
If both fail, the password is expired/revoked — generate a new one.

### "Application-specific password required"

Google returns this when the MAIN account password is used instead of an App
Password. If 2FA is enabled, only App Passwords work for IMAP/SMTP.

**Fix**: Use a 16-character App Password, not the account login password.

## Troubleshooting

### Gmail App Password expired / Invalid credentials

If himalaya fails with `AUTHENTICATIONFAILED` or `Invalid credentials (Failure)`:

```
Error: cannot authenticate to IMAP server using LOGIN mechanism
unexpected NO response: Invalid credentials (Failure)
```

**Cause:** Gmail App Passwords can expire or be revoked. The stored password is no longer valid.

**Fix:**
1. Generate a new App Password at https://myaccount.google.com/apppasswords
2. Update the password file (e.g., `~/.hermes/scripts/gmail-pass.txt`)
3. Test with: `python3 -c "import smtplib, ssl; s=smtplib.SMTP('smtp.gmail.com',587); s.starttls(); s.login('you@gmail.com', open('gmail-pass.txt').read().strip()); print('OK')"`

**Prevention:** Note the password creation date in the password file as a comment, and check annually whether it still works.

### SMTP succeeds but IMAP save-to-Sent fails

If the email sends but himalaya exits with an error about IMAP:
- Check `folder.aliases` syntax (see **Heads up on the alias syntax** above — must use plural `aliases`, not singular `alias`)
- For Gmail Chinese locale: verify actual folder names with `himalaya folder list`

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password. For headless environments where `pass`/GPG is impractical, see `references/headless-password-storage.md`.
- **Gmail Chinese locale pitfall:** Gmail accounts with zh-TW/zh-CN locale use localized folder names. Run `himalaya folder list` to discover the actual names — they may be `[Gmail]/寄件備份` instead of `[Gmail]/Sent Mail`, `[Gmail]/垃圾桶` instead of `[Gmail]/Trash`, `[Gmail]/草稿` instead of `[Gmail]/Drafts`. Always set `folder.aliases` to match the actual server names, or save-to-Sent fails with `unexpected NO response: Folder doesn't exist`.
- **Harmless IMAP warning:** Every command emits `WARN imap_codec::response: Rectified missing 'text' to "..."` — this is an imap-codec library diagnostic, not an error. The command still succeeds. Ignore it.
