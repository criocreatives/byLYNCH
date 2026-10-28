# byLYNCH — current manual AdSense integration

Status verified from production source on 27 October 2026. This is the
maintenance reference; older setup instructions were superseded.

## Configured slots

| Placement | Slot ID | Implementation |
| --- | --- | --- |
| Post metadata strip | `9856514493` | `_includes/manual_ad.html` |
| After the post/gallery | `7038779463` | `_includes/manual_ad.html` |
| Homepage grid, every six genuine photo cards | `8559569688` | `_includes/home_grid_ad.html`, `assets/js/site.js` |

All three IDs are set in `_data/manual_ads.yml`. Do not replace them with
invented values or recreate the units without a separate owner-approved task.

## Rendering rules

- The Google publisher loader is included **once per eligible page** by
  `_layouts/default.html`. The individual HTML ad units do not load the
  external script again.
- On a standard post, there are two owner-approved placements: metadata and
  after-gallery. There are **no ads between photographs**.
- Homepage and its paginated infinite-scroll feed insert a labelled ad card
  after each six real photographic post cards, not after six total grid items.
- `assets/js/site.js` computes available dimensions before requesting each ad
  and selects supported exact creative sizes. Keep any modifications compliant
  with Google's supported ad-sizing documentation; do not crop served ads.
- The nine galleries in `_data/content_flags.yml` must omit the publisher
  script, publisher meta and all post manual ad units. Do not create new E-rated
  exclusions without an explicit editorial/policy decision.
- `_data/content_flags.yml` remains the canonical list, not a classification
  inferred automatically from photo content. The homepage may link to flagged
  posts; advertising policy must be assessed separately.
- Google **Auto Ads** and **Auto optimise** are intended to remain OFF at
  account level. A GitHub build cannot verify account-level settings.
- GA4 loads on public pages independently of advertising eligibility.
  Regional consent and media/privacy handling require browser verification.

## Regression checks

Run `jekyll build --trace` then `python3 scripts/check_site.py`.
Check that eligible posts display the metadata and after-gallery markup, all
nine excluded posts contain zero AdSense code, and the homepage slot ID is
preserved. Test actual fills and behaviour at small/mobile/desktop widths in
the browser. Successful CI does not prove ad fill or policy compliance.

References: `HOMEPAGE_AD_SETUP.md`, `PRIVACY_IMPLEMENTATION.md`, and
Google's documentation at https://support.google.com/adsense/answer/9183363.
