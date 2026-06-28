# Headless Password Storage for Himalaya

## Why pass/GPG is painful headless

`pass` (the password store) relies on GPG, which in headless environments
(SSH, containers, CI runners) often fails with:

- `gpg: cannot open '/dev/tty': No such device or address`
- `gpg: public key decryption failed: Inappropriate ioctl for device`
- `gpg: Sorry, we are in batchmode - can't get input`

These happen because GPG wants to prompt for a passphrase interactively.
Even with `--passphrase ""` (empty passphrase keys), GPG in batch mode
refuses to decrypt without explicit `--pinentry-mode loopback`.

## Practical fallback: cmd + restricted file

Instead of `pass` or keyring, store the password in a file with restricted
permissions and reference it via `backend.auth.cmd`:

```bash
# Store the password — readable only by you
echo -n "your-app-password" > ~/.hermes/scripts/gmail-pass.txt
chmod 600 ~/.hermes/scripts/gmail-pass.txt

# Create the lookup script
cat > ~/.hermes/scripts/gmail-pass.sh << 'SCRIPT'
#!/usr/bin/env bash
cat ~/.hermes/scripts/gmail-pass.txt
SCRIPT
chmod 700 ~/.hermes/scripts/gmail-pass.sh

# Test it
~/.hermes/scripts/gmail-pass.sh
```

Then reference it in `~/.config/himalaya/config.toml`:

```toml
backend.auth.type = "password"
backend.auth.cmd = "~/.hermes/scripts/gmail-pass.sh"
```

Himalaya resolves `~` in `cmd` paths, so the full path works.

## Why this is acceptable

1. **Not in the config file** — the config (which might be backed up,
   committed, or shared) contains no secrets.
2. **Restricted permissions** — `chmod 600` blocks other system users.
3. **Simple** — no GPG key management, no keyring daemon, no tty required.
4. **Easy to rotate** — just overwrite the password file.

## GPG alternative (if tty is available)

If you DO have a tty (desktop, PTY mode), `pass` or `backend.auth.keyring`
are more secure. Use the wizard:

```bash
himalaya account configure
```

Or follow the main `references/configuration.md` for `pass`/keyring setup.