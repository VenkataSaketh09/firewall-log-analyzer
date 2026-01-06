# Sudo Password Configuration

To enable automatic IP blocking with UFW commands, you need to provide the sudo password via environment variable.

## Setup

### Option 1: Environment Variable (Recommended for Development)

Add the sudo password to your `.env` file:

```bash
# Add this line to your .env file
SUDO_PASSWORD=your_ubuntu_password_here
```

**⚠️ Security Warning:**
- Never commit the `.env` file to version control
- The `.env` file should be in `.gitignore`
- For production, consider using passwordless sudo instead (see Option 2)

### Option 2: Passwordless Sudo (Recommended for Production)

Configure passwordless sudo for UFW commands only (more secure):

```bash
# Edit sudoers file
sudo visudo

# Add this line (replace 'saketh' with your username)
saketh ALL=(ALL) NOPASSWD: /usr/sbin/ufw
```

This allows running `ufw` commands without a password, but still requires password for other sudo commands.

### Option 3: Systemd Service with Environment File

If running as a systemd service, create an environment file:

```bash
# Create environment file
sudo nano /etc/firewall-analyzer/sudo-password.env

# Add password
SUDO_PASSWORD=your_password_here

# Secure the file
sudo chmod 600 /etc/firewall-analyzer/sudo-password.env
sudo chown root:root /etc/firewall-analyzer/sudo-password.env

# Update systemd service to load this file
# In your service file, add:
EnvironmentFile=/etc/firewall-analyzer/sudo-password.env
```

## Testing

After setting up, test the IP blocking:

```bash
# Test blocking an IP
curl -X POST http://localhost:8000/api/ip-blocking/block \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"ip_address": "192.168.1.100", "reason": "Test"}'
```

If successful, you should see the IP blocked without password prompts.

## Troubleshooting

### Error: "Sudo password required but SUDO_PASSWORD environment variable is not set"

**Solution:** Add `SUDO_PASSWORD=your_password` to your `.env` file or export it:
```bash
export SUDO_PASSWORD=your_password
```

### Error: "Invalid sudo password"

**Solution:** Check that the password in `SUDO_PASSWORD` matches your system password exactly.

### Error: "Timeout executing UFW command"

**Solution:** 
1. Check if `SUDO_PASSWORD` is set correctly
2. Verify UFW is installed: `which ufw`
3. Test manually: `sudo ufw deny from 192.168.1.100`
4. Consider using passwordless sudo (Option 2) for better reliability

## Security Best Practices

1. **Development:** Use `.env` file (already in `.gitignore`)
2. **Production:** Use passwordless sudo for UFW commands only
3. **Never:** Commit passwords to version control
4. **Rotate:** Change passwords regularly
5. **Restrict:** Use passwordless sudo only for specific commands, not all sudo commands

