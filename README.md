# GetFranchise

GetFranchise is a Canada-focused franchise research and comparison beta. It
helps prospective buyers explore public franchise information, compare a
shortlist, understand evidence quality, and identify what still needs direct
confirmation from a franchisor.

> This is a screening and diligence-planning tool, not investment, legal, or
> financial advice. A higher score or evidence grade is not a recommendation.

## Start here

- **Website source:** `GetfranchiseAi/`
- **Public launch guide:** [`docs/LAUNCH.md`](docs/LAUNCH.md)
- **Image source record:** [`docs/IMAGE_SOURCES.md`](docs/IMAGE_SOURCES.md)
- **Offline research factory:** [`Factory/README.md`](Factory/README.md)

The GitHub Pages build publishes only the browser app, approved public images,
and the reviewed brand export. Private workspace files, local databases,
research reports, environment files, and browser-test artifacts remain out of
the public site.

## Run the website locally

On Windows, run:

```text
run-local.bat
```

Then open the local address printed by the preview window. The app loads the
current public brand export automatically.

## What the beta includes

- A source-aware franchise directory for Canadian buyer research.
- Shortlists, comparisons, and a personal fit questionnaire saved locally in
  the browser.
- Local beta accounts and review notes. These stay on the visitor's browser;
  they are not public reviews or independently verified identities.
- Evidence grades, source links, disclosure boundaries, and confirmation gaps
  so users can see what requires further diligence.

## Repository layout

| Path | Purpose |
| --- | --- |
| `GetfranchiseAi/` | Static browser application, visual assets, and local preview server. |
| `output/franchises/GETFRANCHISE_BRAND_DATA_*.json` | Reviewed public export used by the website. |
| `scripts/build-site.mjs` | Builds the minimal, deployable GitHub Pages bundle. |
| `.github/workflows/deploy-pages.yml` | Builds and deploys the public website from `main`. |
| `Factory/` | Offline publication factory and validation gates. |
| `franchise-intel/` | Research/report generation code and structured source inputs. |
| `docs/` | Launch, research, and operating documentation. |

## Release a site update

1. Review the public export and visual assets.
2. Run `node scripts/build-site.mjs` from the repository root.
3. Test the local site with `run-local.bat`.
4. Commit and push `main`; GitHub Actions publishes the Pages bundle.

For the one-time Pages configuration and full launch checklist, see
[`docs/LAUNCH.md`](docs/LAUNCH.md).

## Research standard

Use exact values only when a source supports the field. Missing, estimated, or
unconfirmed values must remain clearly labelled. Before relying on a profile,
buyers should obtain current Canadian disclosure material, verify the signing
entity, ask about territory and unit economics, and speak directly with the
franchisor and appropriate professional advisers.
