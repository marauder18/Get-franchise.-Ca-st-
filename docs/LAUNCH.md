# GetFranchise launch guide

The public website is the small, static bundle built from `GetfranchiseAi/`.
Only its HTML, JavaScript, stylesheet, logo, and the current reviewed brand
export are published. Research reports, local databases, environment files,
and working artifacts are never included in the Pages artifact.

Selected public visual assets live in `GetfranchiseAi/assets/images/`; the
release builder copies its explicit release list only, deliberately excluding
saved UI screenshots, draft images, and research artifacts.

## One-time GitHub setup

1. Commit and push the launch files to `main`.
2. In the GitHub repository, open **Settings → Pages** and set **Source** to
   **GitHub Actions**.
3. Open the **Actions** tab and run **Deploy public site to GitHub Pages**, or
   let the first push to `main` trigger it.
4. Open the deployment URL reported by the workflow. Add a custom domain in
   GitHub Pages only after the default URL has been verified.

The site keeps the GitHub issue links already configured in `app.js`; verify
that the repository owner/name is still correct before the public launch.

## Release routine

1. Regenerate and validate the franchise export using the existing research
   process.
2. Confirm the dated `GETFRANCHISE_BRAND_DATA_YYYY-MM-DD.json` file contains
   only material suitable for public screening.
3. Run `node scripts/build-site.mjs` from the repository root. The builder
   chooses the newest dated export, copies only launch assets into `site/`, and
   creates a `404.html` fallback for shared links.
4. Test the local UI with `run-local.bat` and check a few profile, search,
   comparison, and issue-reporting flows.
5. Commit the app changes and the reviewed export, then push `main`. The
   deployment workflow publishes the static bundle automatically.

## Before announcing the beta

- Confirm the live deployment loads the directory and a profile on desktop and mobile.
- Confirm both “Request a franchise” and “Report an error” open the correct GitHub issue templates.
- Confirm the Community Reviews beta explains that accounts, logins, and reviews stay on the visitor's browser. Do not describe owner declarations as verified until a server-side identity-review process exists.
- Review the evidence and disclosure wording; this site is screening-only and not investment advice.
- Enable repository branch protection and require a successful Pages deployment before merging launch changes.
- If adding a custom domain, configure HTTPS and its DNS records in GitHub Pages before public promotion.
