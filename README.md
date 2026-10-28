# byLYNCH

byLYNCH is a photography, editorial and cultural archive documenting Jamaican people, art, music and everyday life. It is built with Jekyll and published through GitHub Pages.

**Website:** https://bylynch.com/  
**Repository:** `criocreatives/byLYNCH`  
**Production branch:** `main`  
**Permalinks:** `/YYYY/MM/DD/slug/` (preserved from WordPress)

## Current architecture

*Snapshot verified 28 October 2026: 57 published posts and 10 E-classified posts. Counts are not a substitute for checking the current Git tree.*

| Path | Responsibility |
| --- | --- |
| `_posts/` | Historical articles and galleries, retaining original publication metadata, wording, captions and image order |
| `assets/uploads/` | Source photographs and archival media; never overwrite originals to optimize the site |
| `assets/optimized/covers/` | Separate responsive cover derivatives |
| `_data/featured.yml` | Curated card and hero image assignments |
| `_data/responsive_covers.yml` | Responsive cover files and intrinsic dimensions |
| `_data/card_previews.yml` | Curated, source-derived archive excerpts; no fabricated teasers |
| `_data/people.yml` | People registry and credited appearances; verify identities and associations |
| `_data/content_flags.yml` | Single source of truth for E badges and E-article advertising exclusions |
| `_data/manual_ads.yml` | Three existing Google-issued manual AdSense placements |
| `_layouts/`, `_includes/` | Shared navigation, pages, galleries, SEO metadata and advertising logic |
| `assets/css/site.css` | Shared responsive styles, including the mobile search control |
| `assets/css/about.css`, `assets/css/credits.css` | Page-specific styles |
| `assets/js/site.js` | Navigation, masonry, infinite scroll and manual ad tiles |
| `assets/js/search.js`, `assets/js/lightbox.js` | Site search and accessible photo viewing |
| `scripts/`, `.github/workflows/` | Quality, visual regression, image-derivative and audit tooling |

`_config.yml` excludes the README and internal scripts/workflows from the deployed site.

## Editorial and media rules

- Preserve original photographs, filenames, article language, captions, tags, dates, credits, image order and historical permalinks unless the owner explicitly approves a change.
- Never modify or recompress archival assets in place. `scripts/build_responsive_covers.py` creates separate, incremental derivatives; `scripts/annotate_gallery_dimensions.py` reads actual dimensions, including EXIF orientation.
- Do not fabricate image descriptions or article excerpts. Legacy blank or absent alt text requires image-specific editorial review.
- `_data/card_previews.yml` must remain faithful to original writing. Kråka has no authenticated archive excerpt; Swove in Ledish uses its original iPhone caption.
- Do not restore private or previously restricted articles without individual authorization. In particular, do not publish *Animal* as part of routine cleanup.
- `/romario/` was intentionally removed without a redirect. Do not recreate it incidentally.

### Hermina: explicitly public

`/2017/01/04/hermina/` is a **public** post. It preserves the WordPress timestamp `2017-01-04 03:00:51 -0500`, the original article/gallery structure and 13 supplied original WebPs: four inline photographs, eight gallery photographs, and `img_4444.webp` as both card and hero. Its later owner-approved text edits are part of the published article.

- The post uses `layout: post` and appears in public `search.json` and `sitemap.xml`.
- It **retains** its E classification and `exclude_ads: true`; no site-managed AdSense script or manual units belong on its article page.
- The temporary password gate, locked placeholder and encrypted media are **not** part of current production. Do not restore or redeploy them. Older Git commits/backups may still contain historical encrypted objects; their existence does not authorize publication.
- Historical notes describing Hermina as missing, password-protected or awaiting release are superseded.

## E classifications, advertising and privacy

`_data/content_flags.yml` lists **10** E-classified slugs as of 28 October 2026:

`naked-lady`, `red-october`, `codeine-crazy`, `chocolate`, `lust`, `purplereign`, `bk`, `kraka`, `black-gold`, `hermina`.

E labels appear on relevant cards/posts, and the site-managed AdSense loader and manual placements are excluded from E article pages. This is a technical exclusion, **not** a statement of Google policy approval. Homepage ad tiles can still be near E-labelled cards; review that separately.

Preserve these issued ad slots exactly:

| Placement | Slot |
| --- | --- |
| Post metadata | `9856514493` |
| After the gallery | `7038779463` |
| Homepage/archive tile after each six photo cards (including infinite scroll) | `8559569688` |

The publisher library is loaded once on eligible pages. Keep **Auto Ads and Auto optimise OFF** in the AdSense account unless the owner explicitly changes that decision. The repository cannot establish the current account-dashboard settings or prove ad-policy eligibility.

GA4 uses `G-K95ENNDT6F`. Google Privacy & messaging, consent behaviour, advertising status and regional compliance must be assessed in their respective services and real browsers; a successful Jekyll build cannot certify them. Preserve existing legal/privacy pages and rights-request flows.

## Discovery, mobile and accessibility

- Jekyll produces `sitemap.xml` and `search.json`; `robots.txt` points crawlers to the sitemap. Public Hermina must remain in both generated indexes.
- `_layouts/default.html` handles canonical URLs, descriptions, Open Graph/Twitter data, and schema.org structured data.
- Homepage/archive covers use real image elements and curated mappings. Do not replace them with generated placeholders.
- Search is available on mobile **and** desktop. The phone header displays the search toggle beside the menu; responsive behaviour was verified at 320, 390 and 599 px.
- Preserve the lightbox's keyboard access, Escape handling, focus containment and focus restoration.
- Build-generated asset versioning refreshes cached CSS, JavaScript and search data.
- Search Console coverage and field Core Web Vitals require external verification. CI screenshot/performance measurements are lab evidence, not real-user metrics.

## Testing and release procedure

Supported CI versions: **Jekyll 4.4.1** and **jekyll-paginate 1.1.0** (Ruby 3.3 in GitHub Actions).

```sh
gem install jekyll -v 4.4.1 --no-document
gem install jekyll-paginate -v 1.1.0 --no-document
jekyll build --trace
python3 scripts/check_site.py
node --check assets/js/site.js
node --check assets/js/search.js
node --check assets/js/lightbox.js
node --check assets/js/privacy.js
```

- `.github/workflows/quality-checks.yml` builds Jekyll, runs `scripts/check_site.py` and checks script syntax on `main`, `fix/**`, `seo/**` and pull requests.
- `.github/workflows/visual-regression.yml` runs on `fix/**`, `seo/**` and pull requests. It compares staged desktop/mobile pages and interactions against a freshly fetched production `main` baseline, retaining screenshot and lab-timing artifacts. Intentional visual changes need explicit test coverage.
- `.github/workflows/link-audit.yml` and `scripts/audit_external_links.py` report suspect external links for review. Bot blocks and timeouts are inconclusive; never delete a historical link solely from an automated failure.

**Safe release sequence:**

1. Fetch current `main`, current workflows and applicable branch rules; inspect the exact files to change.
2. Create an exact pre-change backup ref and a scoped `fix/**` staging branch. Limit the diff to the approved change.
3. Run quality checks and desktop/mobile visual regression; inspect failures and intentional differences.
4. Fast-forward `main` without force, using the expected current head. Recheck the branch if it has moved.
5. Verify the **production quality run and GitHub Pages deployment** independently. A successful site build alone is not proof that Pages deployed.

**Branch protection (verified 28 October 2026):** the active `byLYNCH Production Protection` ruleset (ID `26012554`) blocks deletion and non-fast-forward updates on the default branch. It **does not enforce required CI status checks**. Passing staging tests before publication is therefore a release procedure, not an automatic branch rule.

Never force-push `main`, delete rollback history, or treat an earlier handoff SHA as guaranteed current.

## Maintenance history (reference only)

These revisions are historical references, **not** instructions to reset production to an older version.

| Date | Change | Reference |
| --- | --- | --- |
| 27 Oct 2026 | Comprehensive archive/site cleanup; historical `/romario/` removal | `bbc0489`; pre-cleanup backup `backup/bylynch-before-complete-remediation-20261027` (`d65d84a`) |
| 27 Oct 2026 | Earlier reversible cleanup checkpoint | `backup/bylynch-pre-extended-cleanup-20261027` (`a3ab125`) |
| 28 Oct 2026 | Mobile search visibility and interaction correction | `5265870` |
| 28 Oct 2026 | Hermina restored as a public post; temporary encryption removed | `ff1d166`; pre-release backup `backup/bylynch-before-hermina-release-20261028` |
| 28 Oct 2026 | Six owner-authored Hermina text passages updated | `83be8cd`; backup `backup/bylynch-before-hermina-copy-20261028` |

For selective rollback, create a new staging branch and use a scoped `git revert` or targeted file restoration, then rerun the checks. Avoid force-pushing production or wholesale restoration of old encrypted assets.

Historical WordPress exports, old encrypted release packages and original external assets must not be uploaded to the public site as a side effect of maintenance.
