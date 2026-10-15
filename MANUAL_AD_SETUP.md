# byLYNCH manual AdSense placements

Original owner-approved positions: **(1)** inside the white date/tags band beside the post metadata and **(2)** immediately after the entire gallery. No homepage/archive placements, no interruptions of images, and **Auto Ads OFF**.

## Deployment status
Templates and styling are installed, but `_data/manual_ads.yml` intentionally has **blank ad-slot IDs**. Until real numeric AdSense ad-unit IDs are configured, **nothing is displayed, no empty ad spaces are reserved and no extra ad-init script is emitted**. This prevents invented ad IDs and preserves the current visual site.

## Create the 2 units in AdSense
1. AdSense → **Ads** → **By ad unit** → **Display ads**.
2. Create a responsive Display ad unit named `byLYNCH — Post metadata` and select **Responsive**; copy its numeric `data-ad-slot` value.
3. Create a second responsive Display ad unit named `byLYNCH — After gallery`; copy its numeric `data-ad-slot` value.
4. Enter them as quoted strings in `_data/manual_ads.yml`:
   ```yaml
   metadata_slot: "NUMERIC_SLOT_FROM_GOOGLE"
   after_gallery_slot: "NUMERIC_SLOT_FROM_GOOGLE"
   ```
5. Commit and deploy, keeping AdSense → **Auto ads** OFF and **Auto optimise** OFF.

The common publisher script `ca-pub-4888519100229596` is already in `_layouts/default.html`. The `_includes/manual_ad.html` component adds only the ad unit markup and the corresponding `adsbygoogle.push({})`. Do **not** duplicate the common external script.

## Exclusions and rendering
- Both placements are omitted on the nine slugs in `_data/content_flags.yml`, even if IDs are set.
- The shared AdSense publisher script is also omitted on those nine galleries.
- They do not appear on the homepage or archive, only on eligible post pages.
- The first unit uses Google's responsive `horizontal` shape (fixed width limit in CSS), with no overlay on date or tags; it stacks below the text on small viewports but stays within the white band.
- The second unit uses a responsive display shape in its own block **after** the complete image/masonry gallery and **before** archived comments/adjacent-post navigation.
- The site's post-body content, photography, captions, metadata values, XML previews, and featured covers are unchanged.

## QA before calling this revenue-live
- Check rendering at small mobile and wide desktop widths after enabling slots, including metadata bar growth if a creative becomes tall.
- Verify each eligible post page requests only its two configured manual ad units; no Auto Ads overlay or automatic insertion.
- Inspect all nine excluded gallery post HTML outputs for zero `adsbygoogle` unit markup and zero Google publisher script.
- Respect Google ads policy on page context/site eligibility; publisher approval does not guarantee compliance for explicit photography.
- Use AdSense reports to check ad-unit-specific impressions once ads begin serving.

Google documents: https://support.google.com/adsense/answer/9274025 and https://support.google.com/adsense/answer/9183460.
