# Lugano Parking – website package

Everything in this folder is the app. Put the folder online and it works.

## Option A: GitHub Pages (free, 5 minutes)
1. Go to github.com and sign in (or create a free account).
2. Click "New repository", name it `lugano-parking`, keep it Public, click "Create repository".
3. On the empty repository page click "uploading an existing file", drag in ALL the files from this folder (index.html, manifest.webmanifest, the three icon PNGs), then click "Commit changes".
4. Open Settings → Pages. Under "Build and deployment" choose Branch: `main`, folder `/ (root)`, click Save.
5. After about a minute the page shows your link: `https://YOUR-USERNAME.github.io/lugano-parking/`. Send that to your friends.

## Option B: Netlify Drop
Go to app.netlify.com/drop, sign in, and drag this whole folder onto the page. You get a link immediately.

## What happens online
On a real website the app reads the Città di Lugano live feed directly, so the free spots refresh every 3 minutes and whenever the app is reopened. Friends can add it to their home screen (Share → Add to Home Screen on iPhone, "Install app" on Android) and it opens full screen like a native app.
