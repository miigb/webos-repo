# webOS Homebrew Channel Repository

Custom repository for LG Smart TVs running webOS with **Homebrew Channel**.

## How to Add to Your LG TV

1. Open **Homebrew Channel** on your LG TV.
2. Click the **Settings** icon in the top right corner.
3. Scroll to **Repositories** and click **Add Repository**.
4. Enter the URL:
   ```
   https://miigb.github.io/webos-repo/
   ```
   *(Or direct manifest: `https://miigb.github.io/webos-repo/api/apps.json`)*
5. Click **Add** and return to the main catalog.
6. Your custom apps will now appear in the Homebrew store!

---

## Included Packages (Active Catalog in `apps.json`)

| App | Package File | Version | Architecture / Target | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **VortX TV (Pre-Configured)** | `com.vortx.tv_0.4.0_all.ipk` | `0.4.0` | Universal webOS (Chrome 79+) | Baked-in Stremio Cloud, Synology NAS (`:8095` / `:11470`), and Plex (`:32400`) |
| **Xbox Cloud Gaming** | `com.redphx.better-xcloud_6.2.2_all.ipk` | `6.2.2` | Universal webOS (Chrome 79+) | Real-time transpilation via Synology NAS bridge (`:8097`/`:8095`) |
| **YouTube AdFree (Universal Web)** | `youtube.leanback.v4_0.8.4_all.ipk` | `0.8.4` | webOS 3.0 - 6.0 (`_all.ipk`) | **Verified working flavor** on LG `55UP77006LB` (from `NicholasBly/youtube-webos`) |
| **Lampa** | `lampa.tv_2.3.0_all.ipk` | `2.3.0` | Universal webOS | Connected to NAS TorrServer (`:8090`) & Subtitle Proxy (`:8095`) |
| **Doorbell PiP** | `com.doorbell.pip_1.1.0_all.ipk` | `1.1.0` | Universal webOS | Multi-camera (Ring + Eufy) Picture-in-Picture overlay |
| **Nuvio TV** | `space.nuvio.webos_1.2.3_all.ipk` | `1.2.3` | Universal webOS | Native media center with Stremio addon support |
| **Homebrew Channel (Custom)** | `org.webosbrew.hbchannel_0.7.3_all.ipk` | `0.7.3` | Universal webOS | Pre-configured with `https://miigb.github.io/webos-repo/api/apps.json` & `webosappclub` |

---

## 1-Click Disaster Recovery & Agent Guidelines

If an LG firmware update or Developer Mode expiration ever clears your apps:
- Double-click **`~/Desktop/Restore LG TV.command`** on your Mac.
- Full details & troubleshooting: See **[LG TV Recovery Guide](file:///Users/miguelbrito/Development/DS218/webos-repo/LG_TV_RECOVERY_GUIDE.md)**.
- AI Model Packaging & Chrome 79 Rules: See **[AGENTS.md](file:///Users/miguelbrito/Development/DS218/webos-repo/AGENTS.md)**.

---

## Live Web Preview

Visit the web interface: **[https://miigb.github.io/webos-repo/](https://miigb.github.io/webos-repo/)**
