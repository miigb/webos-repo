# AGENTS.md — LG webOS Homebrew Repository & Packaging Rules

> **MANDATORY INSTRUCTIONS FOR ALL AI MODELS**
> Read these rules carefully before modifying or packaging any `.ipk` application for the user's LG Smart TV (`55UP77006LB`, `webOS 6.5.3` / `Chrome 79` at `192.168.1.137`).

---

## 🚨 1. Strict LG webOS 6.0 (`Chrome/79.0.3945.79`) Packaging Rules

1. **Never Use `<script type="module">` on `file://` Origins**:
   - Packaged webOS apps execute on `file:///media/developer/apps/usr/palm/applications/<app-id>/index.html`.
   - Chromium on `file://` blocks ES module scripts due to CORS (`origin 'null'`).
   - Always load bundles using `<script defer src="./assets/..."></script>`.
2. **Eliminate `import.meta` Before Packaging**:
   - In non-module `<script defer>` tags, any occurrence of `import.meta` (such as Vite's `import.meta.url` inside worker or preload wrappers) triggers an immediate **parse-time `Uncaught SyntaxError: Cannot use 'import.meta' outside a module`**, aborting the entire bundle and leaving a blank screen after the splash screen.
   - Always replace `import.meta.url` with `(document.currentScript&&document.currentScript.src||location.href)` and verify `grep -c "import.meta" bundle.js` returns `0`.
3. **Always Transpile JS & CSS to `--target=chrome79`**:
   - Modern Vite/Rollup bundles use ES2021+ and modern CSS syntax unsupported by Chrome 79.
   - Always run:
     ```bash
     npx --yes esbuild input.js --target=chrome79 --minify --outfile=output.js
     npx --yes esbuild input.css --target=chrome79 --minify --outfile=output.css
     ```
4. **Always Polyfill Post-Chrome-79 Web APIs Before the Main Bundle**:
   - Inject an inline `<script>` before the bundle that polyfills:
     - `AbortSignal.timeout(ms)` (added in Chrome 103)
     - `crypto.randomUUID()` (undefined on non-secure `file://` origins)
     - `Object.hasOwn()`, `String.prototype.replaceAll()`, `Array.prototype.at()`
5. **Allow `http://` LAN Addon & Media URLs**:
   - Replace strict `/^https:\/\//i` regex validators with `/^https?:\/\//i` so local Synology NAS endpoints (`http://192.168.1.147:8095/...`, `http://192.168.1.147:11470/...`, `http://192.168.1.147:32400/...`) work natively.

---

## 📦 2. VortX TV (`com.vortx.tv` `v0.2.0`) Pre-Configured Architecture

`com.vortx.tv` (`v0.2.0`) is pre-configured out of the box so the user never has to type settings on the TV remote:
- **Streaming Server (`vortx.web.streamingServerUrl`)**: `http://192.168.1.147:11470` (Synology DS218 `rivulet-engine v0.27.1`).
- **TV Layout Mode (`vortx.tv.force`)**: `"1"`.
- **Pre-Seeded & Live-Synced Addons (`vortx.web.addons.v1`)**:
  - Synced automatically on startup from `http://192.168.1.147:8095/api/vortx/bootstrap`:
    1. `Cinemeta` (`https://v3-cinemeta.strem.io/manifest.json`)
    2. `⭐ My IMDb Watchlist (LG TV Safe)` (`http://192.168.1.147:8095/stremio/imdb/manifest.json`)
    3. `🏠 Synology NAS & Plex Library` (`http://192.168.1.147:8095/stremio/plex/manifest.json`)
    4. `IMDB Catalogs` (`https://1fe84bc728af-imdb-catalogs.baby-beamup.club/manifest.json`)
    5. `Anime Kitsu` (`https://anime-kitsu.strem.fun/manifest.json`)
    6. `⚡ NAS Stream Booster (LG TV Safe)` (`http://192.168.1.147:8095/stremio/manifest.json`)
    7. `Torrentio (LG TV Safe)`
    8. `TorrentsDB`
    9. `ThePirateBay+`
    10. `💬 NAS Subtitles Suite (EN/RU/ES/PT)` (`http://192.168.1.147:8095/stremio/subs/manifest.json`)
    11. `OpenSubtitles v3`
    12. `OpenSubtitles PRO (EN/RU/ES/PT)`
- **2-Way Scrobbling (`window.__vortxScrobble`)**:
  - Hooks into VortX's `Ht(e,t,i)` progress updater and posts playback progress to `http://192.168.1.147:8095/api/plex/scrobble`, syncing watch history to **Stremio Cloud, Plex, and Trakt**.

---

## 🚀 3. Release Checklist for `webos-repo`

1. Package with `ares-package --no-minify <app-dir> -o /tmp/`.
2. Test directly on the TV first:
   ```bash
   ares-setup-device -m tv -i "host=192.168.1.137"
   ares-install -d tv /tmp/<package>.ipk
   ares-launch -d tv <app-id>
   ```
3. Copy `.ipk` to `packages/`, compute `shasum -a 256` and `stat -f%z`, update `manifests/<id>.manifest.json`, `apps.json`, and `index.html`.
4. Commit and push to `origin main` (`https://github.com/miigb/webos-repo.git`).
