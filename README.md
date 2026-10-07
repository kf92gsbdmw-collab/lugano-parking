# Lugano Parking – website package

Everything in this folder is the app. Put the folder online and it works.

## Option A: GitHub Pages (free, 5 minutes)
1. Go to github.com and sign in (or create a free account).
2. Click "New repository", name it `lugano-parking`, keep it Public, click "Create repository".
3. On the empty repository page click "uploading an existing file", drag in ALL the files from this folder (index.html, sw.js, manifest.webmanifest, the three icon PNGs and the `tiles`, `scripts` and `.github` folders), then click "Commit changes".
4. Open Settings → Pages. Under "Build and deployment" choose Branch: `main`, folder `/ (root)`, click Save.
5. After about a minute the page shows your link: `https://YOUR-USERNAME.github.io/lugano-parking/`. Send that to your friends.

## Option B: Netlify Drop
Go to app.netlify.com/drop, sign in, and drag this whole folder onto the page. You get a link immediately.

## What happens online
On a real website the app reads the Città di Lugano live feed directly, so the free spots refresh every 3 minutes and whenever the app is reopened. Friends can add it to their home screen (Share → Add to Home Screen on iPhone, "Install app" on Android) and it opens full screen like a native app.

## Files
- `index.html`: the app (about 85 KB). Three views: Garages (live free spots), Going to (pick a destination and how long you stay, get the garages ranked by walking time, space and price; place search uses the free Photon geocoder, walking times are distance estimates), Street (blue zone and meter rules).
- `sw.js`: service worker. Makes the second open instant and keeps the map available offline. Bump `VERSION` inside it whenever you change files.
- The map is a vector basemap from OpenFreeMap (free, no API key, attribution included), light and dark styles. `tiles/z14.jpg` to `z17.jpg` are the offline fallback: an OpenStreetMap snapshot of the centre that is shown when there is no network.
- `logo.svg`, `icon-*.png`: the app icon. `logo-wordmark.png` is for sharing and is not needed on the site.
- `manifest.webmanifest` and the icons: home screen install.
- `scripts/` and `.github/workflows/log-occupancy.yml`: a GitHub Action that reads the city feed every 10 minutes and keeps the history on a separate `data` branch (so the website is not rebuilt each time). It also writes `typical.json` there, which the app reads to show typical occupancy per weekday and hints like "usually full from 10:00". Nothing to configure: once the workflow file is on `main`, GitHub runs it. First patterns appear after about two weeks of readings. GitHub pauses scheduled workflows after 60 days without any commit to the repo; a push (or pressing "Run workflow" under Actions) wakes it up again.
