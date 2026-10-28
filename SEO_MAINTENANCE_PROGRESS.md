# SEO foundation and production safeguards

> **Historical progress log.** Items dated 15 October represent the state *at
> that time*, not the current TODO list. For current build/runtime architecture
> consult `README.md`, `MANUAL_AD_SETUP.md` and `scripts/check_site.py`.
>
> **27 October 2026:** 56 published posts; 56 curated cover entries with 480px
> and 960px WebP derivatives, plus distinct hero variants where configured.
> Gallery WebP derivatives exist for the four recently published collections.
> Manual advertising is configured in three placements, including homepage
> tiles. The Jekyll regression suite verifies all 56 archive preview entries
> against `_data/card_previews.yml` and excludes repository-only source files
> from the public site build. Browser-based visual, Core Web Vitals and
> regional consent checks remain separate. GitHub `main` branch protection
> still requires repository administrator configuration.


## Implemented (15 October 2026)
- Site-generated `/sitemap.xml` from Jekyll pages and all public posts.
- `/robots.txt` with the canonical sitemap URL.
- Homepage and archive cards now expose the existing curated cover files as regular, crawlable `<img src>` tags with a descriptive functional alt. Their established 4:5 crop and photographic choices are unchanged.
- Each home/archive listing has one visually hidden H1; card titles are H2. Individual gallery titles remain H1.
- Shared canonical/description metadata now includes Open Graph, Twitter card, and BlogPosting/WebSite JSON-LD structured data.
- Automated Jekyll build checks enforce presence of 52 public posts, known cover assets, discovery files, metadata, and **no AdSense code on nine E-flagged gallery pages**.
- Updated repository README for current production deployment.

## Not yet implemented or measured
- Content-specific alt text for individual gallery photographs. Cover alts are functional; an editorial pass remains necessary to describe each image accurately.
- Responsive WebP/AVIF derivatives and a resizing pipeline; all existing photographs remain original.
- Core Web Vitals or Lighthouse testing in a real browser, plus Search Console indexing/coverage measurement.
- Account-level verification in Google Search Console. Submit `https://bylynch.com/sitemap.xml` after checking the live URL.
- Branch protection/rulesets. These are GitHub repository settings and were not changed in code.
- Automated full link crawling and actual mobile screenshot regression tests.
- Image-policy/editorial classification beyond the current nine flags.

## Release validation
1. Push changes first to `seo/phase1-discovery-templates-ci-20261015`.
2. Confirm its **Build and validate byLYNCH** workflow passes.
3. Review changed files and confirm no `_posts/`, `assets/uploads/`, featured cover remappings or manual-ad data were touched.
4. Fast-forward `main` and confirm the native GitHub Pages deployment succeeds.
5. Open site in browser at mobile and desktop sizes to check native image crop and ads.
6. Verify public `robots.txt` and `sitemap.xml`, then submit the sitemap in Search Console.

Notes: A passing build is not proof that Google has indexed every page, that Search Console is configured, or that Core Web Vitals meet thresholds.

## Performance pass — 15 October 2026
- 52 curated covers now have 480px and 960px WebP derivatives under `assets/optimized/covers/` (104 files), with actual widths and dimensions in `_data/responsive_covers.yml`.
- Homepage/archive tiles use a `<picture>` WebP source and the original JPG/PNG fallback. The original cover selection, image order, 4:5 crop and overlay treatment remain unchanged.
- On mobile (up to 767px), single-post hero images select optimized WebP variants; wider devices retain original full-resolution hero image.
- A reproducible `scripts/build_responsive_covers.py` generator and `.github/workflows/optimize-covers.yml` pipeline generate/commit derivatives on `seo/performance-*` staging branches (also supports manual workflow dispatch). Future cover changes must refresh the manifest and derivatives before publishing.
- Moved Google Fonts out of CSS `@import` into the HTML head with preconnect; retained the identical Lato weights and `display=swap`. Deferred the main site script without changing event handlers.
- The quality workflow verifies the expected 104 WebP files, responsive picture markup, source fallbacks, metadata and nine explicit-gallery ad exclusions.
- **Not part of this phase:** 993 gallery originals remain unchanged. No claim of improved Lighthouse/Core Web Vitals score until real measurements are obtained.
