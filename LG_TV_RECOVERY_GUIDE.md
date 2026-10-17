# 📺 LG TV webOS Homebrew & Disaster Recovery Guide

Comprehensive reference for managing, troubleshooting, and restoring homebrew applications and repositories on the LG Smart TV (**LG 55UP77006LB**, webOS 6.5.3 / firmware 03.53.45).

---

## ⚡ Quick 1-Click Recovery

If a webOS system update or Developer Mode session expiration wipes your apps:

1. **Turn on the TV** and open the **Developer Mode** app.
2. Ensure **Dev Mode Status: ON** and toggle **Key Server: ON**.
3. On your Mac, double-click:
   ```
   ~/Desktop/Restore LG TV.command
   ```
   *(Points to `/Users/miguelbrito/Downloads/Software/webOS/restore-lg-tv.sh`)*
4. If prompted, type the **6-character Passphrase** shown on your TV screen.
5. Done! In ~15 seconds, all apps and repositories are automatically restored and verified.

---

## 🖥️ Target Device Specs

| Property | Value |
| :--- | :--- |
| **Model** | LG 55UP77006LB |
| **webOS SDK Version** | 6.5.3 (board: `K7LP_DVB_EU`) |
| **Firmware** | 03.53.45 |
| **IP Address** | `192.168.1.137` *(fallback `192.168.1.132`)* (Wireless) |
| **SSH Port** | `9922` (User: `prisoner`) |
| **Key Server Port** | `9991` (HTTP endpoint `/webos_rsa`) |

---

## 📦 Installed Applications Catalog

All `.ipk` binaries are version-controlled and preserved in:
`/Users/miguelbrito/Downloads/Software/webOS/` and `webos-repo/packages/`.

| App Name | Package ID | Version | Description & Notes |
| :--- | :--- | :--- | :--- |
| **Homebrew Channel** | `org.webosbrew.hbchannel` | `0.7.3` | Sideload installer. **Custom-repacked** to have the Lampa repo (`webosappclub`) pre-configured into default repositories. |
| **Lampa** | `lampa.tv` | `2.3.0` | Movie/TV media catalog. Interfaces with Synology TorrServer Matrix (`192.168.1.147:8090`) & Lampa Subtitle Proxy (`192.168.1.147:8095`). |
| **YouTube AdFree** | `youtube.leanback.v4` | `0.8.2` | Ad-free YouTube player with SponsorBlock integration. |
| **Doorbell PiP** | `com.doorbell.pip` | `1.1.0` | Picture-in-picture camera overlay from Home Assistant / Synology media stack. |
| **Nuvio TV** | `space.nuvio.webos` | `1.2.3` | Lightweight, native media center & streaming library with Stremio add-on ecosystem. |
| **VortX TV** | `com.vortx.tv` | `0.3.0` | Native 10-foot VortX TV streaming app with auto-bootstrapped Stremio Cloud, native Plex (`192.168.1.147:32400`), Synology DS218 Stremio Engine (`192.168.1.147:11470`), and Chrome 79 spatial D-Pad navigation. |

---

## 🌐 Configured Repositories

1. **Official webOS Homebrew:**
   `https://repo.webosbrew.org/api/apps.json`
2. **WebOS App Club (Lampa & TorrServer Repo):**
   `https://webosappclub.github.io`
   *(Pre-baked into Homebrew Channel package; also manually addable via Settings ⚙️ $\rightarrow$ Add Repository)*
3. **Personal DS218 Custom Repo:**
   `https://miigb.github.io/webos-repo/`
   *(Direct manifest: `https://miigb.github.io/webos-repo/api/apps.json`)*

---

## 🔧 Under the Hood: Why Developer Mode Connections Fail & How We Fixed It

### 1. The "Failed to fetch private key" Error in webOS Dev Manager
* **Root Cause:** The desktop app tries to fetch the RSA private key over HTTP from `http://<TV_IP>:9991/webos_rsa`. On macOS, TCP streaming/socket handling in the app frequently causes this request to time out or fail to parse.
* **Fix:** The key is fetched directly via `curl` and decrypted with the passphrase:
  ```bash
  curl -s "http://192.168.1.132:9991/webos_rsa" -o /tmp/webos_rsa_enc
  openssl rsa -in /tmp/webos_rsa_enc -passin "pass:<PASSPHRASE>" -traditional -out ~/.ssh/tv_webos
  chmod 600 ~/.ssh/tv_webos
  ```
  *(Note: `-traditional` ensures the output is PKCS#1 RSA format `-----BEGIN RSA PRIVATE KEY-----` which Node.js `ssh2` and `ares-cli` require, rather than PKCS#8).*

### 2. SSH "no matching host key type found"
* **Root Cause:** Modern macOS OpenSSH disables the legacy `ssh-rsa` (SHA-1) signature algorithm. webOS runs an older OpenSSH server offering only `ssh-rsa`.
* **Fix:** Configured in `~/.ssh/config`:
  ```ssh-config
  Host lg-tv
    HostName 192.168.1.132
    Port 9922
    User prisoner
    IdentityFile ~/.ssh/tv_webos
    HostKeyAlgorithms +ssh-rsa
    PubkeyAcceptedKeyTypes +ssh-rsa
  ```

---

## 🛠️ Useful Terminal Commands

```bash
# 1. Connect directly to TV shell
ssh lg-tv

# 2. Check TV system info via ares CLI
ares-device -i --device tv

# 3. List installed developer packages
ares-install --device tv -l

# 4. Install an application package
ares-install --device tv /path/to/package.ipk

# 5. Launch an installed application
ares-launch --device tv org.webosbrew.hbchannel
ares-launch --device tv lampa.tv
ares-launch --device tv youtube.leanback.v4
ares-launch --device tv com.doorbell.pip

# 6. Close an application
ares-launch --device tv --close org.webosbrew.hbchannel
```

---

## 🔄 How to Use webOS Dev Manager GUI (Alternative)

If you ever prefer the graphical **webOS Dev Manager** desktop app:
1. Open the app and click **Add Device** (or edit existing `tv`).
2. Set:
   - **Name:** `tv`
   - **Host:** `192.168.1.132`
   - **Port:** `9922`
   - **Username:** `prisoner`
   - **Authentication:** Switch from `Dev Mode` to **`SSH Key`** (or `Private Key`).
3. Select the key file:
   ```
   /Users/miguelbrito/.ssh/tv_webos
   ```
4. Leave passphrase blank (it is already decrypted). Click **Finish**.
