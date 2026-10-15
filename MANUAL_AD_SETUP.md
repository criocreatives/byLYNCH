# byLYNCH manual AdSense placements

Original owner-approved positions: **(1)** inside the white date/tags band beside the post metadata and **(2)** immediately after the entire gallery. No homepage/archive placements, no interruptions of images, and **Auto Ads OFF**.

## Deployment status
Both manual AdSense units are **activated** in `_data/manual_ads.yml` with the Google-issued slot IDs supplied by the owner:
- **Post metadata** — `9856514493`.
- **After gallery** — `7038779463`.

The site's common AdSense loader remains in the shared `_layouts/default.html` head, and the manual units are emitted only on eligible post pages. Both units use Google's supplied `data-ad-format="auto"` and `data-full-width-responsive="true"`. **"auto" in data-ad-format means responsive sizing of this manual unit; it does not enable Google Auto Ads.** Ad display and fill depend on Google, network conditions and advertiser availability.

## Create the 2 units in AdSense
1. AdSense → **Ads** → **By ad unit** → **Display ads**.
2. Create a responsive Display ad unit named `byLYNCH — Post metadata` and select **Responsive**; copy its numeric `data-ad-slot` value.
3. Create a second responsive Display ad unit named `byLYNCH — After gallery`; copy its numeric `data-ad-slot` value.
4. Slots `9856514493` and `7038779463` have been added to `_data/manual_ads.yml` and deployed.
5. Keep AdSense → **Auto ads** OFF and **Auto optimise** OFF.

The common publisher script `ca-pub-4888519100229596` is already in `_layouts/default.html`. The `_includes/manual_ad.html` component adds only the ad unit markup and the corresponding `adsbygoogle.push({})`. Do **not** duplicate the common external script.

## Exclusions and rendering
- Both placements are omitted on the nine slugs in `_data/content_flags.yml`, even if IDs are set.
- The shared AdSense publisher script is also omitted on those nine galleries.
- They do not appear on the homepage or archive, only on eligible post pages.
- The first unit uses Google's `auto` responsive ad format, with a 440px CSS width limit to preserve the date/tags layout. It stacks below the text on small viewports while staying within the white band. Ad height may vary depending on Google's response.
- The second unit also uses Google's `auto` responsive ad format in its own block **after** the complete image/masonry gallery and **before** archived comments/adjacent-post navigation.
- The site's post-body content, photography, captions, metadata values, XML previews, and featured covers are unchanged.

## QA before calling this revenue-live
- Check rendering at small mobile and wide desktop widths after enabling slots, including metadata bar growth if a creative becomes tall.
- Verify each eligible post page requests only its two configured manual ad units; no Auto Ads overlay or automatic insertion.
- Inspect all nine excluded gallery post HTML outputs for zero `adsbygoogle` unit markup and zero Google publisher script.
- Respect Google ads policy on page context/site eligibility; publisher approval does not guarantee compliance for explicit photography.
- Use AdSense reports to check ad-unit-specific impressions once ads begin serving.

Google documents: https://support.google.com/adsense/answer/9274025 and https://support.google.com/adsense/answer/9183460.
