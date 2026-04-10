# WSL2 DNS resolution failures on Windows 19045

**Problem:** WSL2 cannot resolve hostnames (`curl: (6) Could not resolve host`), blocking package installation (apt, pip, npm, cargo, poetry, etc.). Affects Ubuntu, Debian distributions on Windows build 19045.


## Related issues

This pattern (WSL2 DNS + VPN) common across Windows development. Same fix applies to:
- npm/pip/cargo package installation
- git clone from GitHub/GitLab
- curl/wget downloads
- apt/yum package managers

## Root cause

Windows 10 build 19045 doesn't support WSL2 mirrored networking mode. WSL2 auto-generates `/etc/resolv.conf` pointing to Windows DNS server, which often fails (VPN interference, corporate DNS restrictions, or Windows DNS not forwarding to external resolvers).

**Symptoms:**
```bash
# Example with Poetry, but applies to any package installer
curl -sSL https://install.python-poetry.org | python3 -
# curl: (6) Could not resolve host: install.python-poetry.org

sudo apt update
# Temporary failure resolving 'security.ubuntu.com'

npm install
# getaddrinfo ENOTFOUND registry.npmjs.org
```

## Solution: Manual DNS configuration

Disable auto-generated `resolv.conf` and use Google DNS directly:

```bash
# Step 1: Disable WSL2 auto-generated resolv.conf
sudo tee /etc/wsl.conf > /dev/null <<EOF
[network]
generateResolvConf = false
EOF

# Step 2: Exit WSL and restart
exit
wsl --shutdown
wsl

# Step 3: Configure DNS manually
sudo rm /etc/resolv.conf  # Remove auto-generated file
sudo tee /etc/resolv.conf > /dev/null <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

# Step 4: Make immutable (prevent auto-regeneration)
sudo chattr +i /etc/resolv.conf

# Step 5: Verify
curl https://www.google.com  # Should return HTTP/2 301
```

**Critical:** `chattr +i` makes file immutable. Without this, WSL2 may regenerate `/etc/resolv.conf` on restart.

## Alternative: Use Windows DNS with VPN disabled

If VPN is the blocker:
```bash
# /etc/resolv.conf
nameserver 192.168.x.x  # Windows host IP (from ipconfig)
```

Then disable VPN temporarily for WSL2 operations. Re-enable after package installation.

## Why mirrored networking doesn't work

Windows 19045 doesn't support these `.wslconfig` options:
```ini
# ❌ Won't work on Windows 19045
[wsl2]
networkingMode=mirrored
dnsTunneling=true
firewall=true
autoProxy=true
```

These require Windows 11 or Windows 10 build 22000+. Check version:
```powershell
winver  # Must show 22000+ for mirrored networking
```

## VPN interference patterns

VPN software often blocks WSL2 networking completely:

**Symptoms:**
- DNS resolution fails even with Google DNS
- All external connections timeout
- Windows host has internet, WSL2 doesn't

**Solutions:**
1. Disable VPN temporarily for WSL2 operations
2. Configure VPN to allow WSL2 traffic (if supported)
3. Use VPN split tunneling to exclude WSL2
4. Use CI/CD instead of local WSL2

## Python-specific issue: `python` vs `python3`

Many tools (Poetry, pip, pyenv, etc.) look for `python` command, Ubuntu provides only `python3`:

```bash
# Create symlink
sudo ln -sf /usr/bin/python3 /usr/bin/python

# Verify
python --version  # Should show Python 3.x.x
```

Without this, Python tool installations fail with `[Errno 2] No such file or directory: 'python'`.

## Complete WSL2 setup for testing

After DNS fix:

```bash
# 1. Install your dependency manager (example: Poetry)
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/root/.local/bin:$PATH"
# Or use pip, npm, cargo, etc. for your project

# 2. Python symlink (if using Python tools)
sudo ln -sf /usr/bin/python3 /usr/bin/python

# 3. Install Docker Engine directly in WSL2 (no Docker Desktop needed)
# Add Docker's official GPG key
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo service docker start

# Add user to docker group (optional, avoids sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker run hello-world

# 3. Install project dependencies
cd /mnt/c/your/project/path  # Adjust to your Windows project path
poetry install --with test --no-interaction  # Or npm install, cargo build, etc.

# 5. Run tests (Docker now available)
poetry run pytest tests/ -v  # Or npm test, cargo test, etc.
```

## Docker options for WSL2

### Option 1: Docker Engine in WSL2 (recommended)
**Install directly in Ubuntu/Debian via apt:**
- No Docker Desktop required
- No GUI configuration needed
- Fully automated via command line
- Can be scripted and used by LLMs
- Runs natively in WSL2
- Lighter weight

**Why recommended:** Docker Desktop requires manual GUI steps (Settings → WSL Integration → Enable) which cannot be automated or performed by LLMs. Docker Engine installation is 100% scriptable.

**Start Docker on WSL2 launch:**
```bash
# Add to ~/.bashrc or ~/.zshrc
if ! service docker status > /dev/null 2>&1; then
    sudo service docker start
fi
```

### Option 2: Docker Desktop with WSL2 integration (NOT recommended)
**Use existing Docker Desktop:**
- ❌ Requires manual GUI step: Docker Desktop → Settings → Resources → WSL Integration → Enable distribution
- ❌ Cannot be automated via scripts
- ❌ Cannot be performed by LLMs
- ❌ Must be done manually each time you create new WSL distribution
- ✅ Shares Docker daemon between Windows and WSL2 (only benefit)
- ✅ Good if already using Docker Desktop on Windows

**Use only if:** You already have Docker Desktop running and want to share the daemon with Windows host.

**For automation/LLM workflows:** Use Option 1 (Docker Engine) instead.

## Debugging DNS issues

Check current DNS configuration:
```bash
# See what WSL2 is using
cat /etc/resolv.conf

# Test DNS resolution
nslookup google.com
dig google.com

# Test HTTP
curl -v https://www.google.com

# Check if wsl.conf exists
cat /etc/wsl.conf
```

If `resolv.conf` keeps reverting, check if it's immutable:
```bash
lsattr /etc/resolv.conf
# Should show: ----i--------e----- /etc/resolv.conf
#                   ^ immutable flag
```

## When WSL2 is worth the effort

**Use WSL2 if:**
- Need genuine Linux environment for development
- Multiple projects require Linux tooling
- CI/CD not available or too slow
- Learning Linux commands

**Skip WSL2 if:**
- Only need 5 specific tests to pass
- CI/CD available (GitHub Actions)
- VPN can't be disabled
- Windows build < 19045 or DNS issues persist

For single test coverage gap, CI/CD is more practical (zero setup, always works).

## Error patterns

### DNS resolution fails even after fix
**Cause:** VPN or corporate firewall blocking all external DNS
**Solution:** Disable VPN or use CI/CD

### `resolv.conf` keeps reverting
**Cause:** Not immutable
**Solution:** `sudo chattr +i /etc/resolv.conf`

### Docker not available in WSL2
**Cause:** No Docker installed or Docker Desktop integration not enabled  
**Solution 1 (recommended):** Install Docker Engine directly in WSL2 (see complete setup above)  
**Solution 2:** Docker Desktop → Settings → WSL Integration → Enable distribution

### Poetry can't find Python
**Cause:** Missing `python` symlink (applies to many Python tools)  
**Solution:** `sudo ln -sf /usr/bin/python3 /usr/bin/python`

### Tests skip due to "Docker not available"
**Cause:** `docker_or_skip` fixture correctly detects missing Docker  
**Solution:** Install Docker Engine in WSL2 (apt) or enable Docker Desktop WSL integration (GUI step)

