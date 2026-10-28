# byLYNCH — Homepage grid ad (one after six posts)

## Activated: 15 October 2026
- Google-provided homepage slot: `8559569688`.
- Both initial and infinite-scroll tiles now use **exact supported ad sizes** selected from the card's available width *before* requesting an ad.
- Removed `data-ad-format="auto"` and `data-full-width-responsive="true"` from the slots: those made the served creative expand outside the 4:5 tile on mobile.
- Sizes used inside the unchanged 4:5 tile: 300×250, 250×250, 200×200 or 180×150. No ad iframe is cropped, stretched, covered or resized after rendering.
- Individual post metadata uses a compact 320×100 or 234×60 ad; after-gallery uses a supported 728×90, 468×60, 300×250, 250×250 or 200×200 format depending on its available width.
- This follows Google's permitted exact-size responsive-code modifications: https://support.google.com/adsense/answer/9183363.
- No extra publisher script was added; the existing sitewide loader is reused once.
- Existing post metadata and after-gallery slot IDs are preserved.
- Google may take time to serve creatives; zero ad fill does not necessarily mean an installation error.

## Historical setup steps (unit already exists)
**Do not repeat this setup for an already-configured slot.** The steps below record the original provisioning process, not an outstanding task.

1. AdSense → Ads → **By ad unit** → **Display ads**.
2. Name: `byLYNCH — Homepage Grid (6 Cards)`.
3. Ad size: **Responsive** (not Fixed). The **Square** layout preview is closest to the site's 4:5 portrait tiles; the preview does not fix the served creative's dimensions.
4. Save and get code. Send the numeric **data-ad-slot** ID from that code.
5. The unit is now activated in `_data/manual_ads.yml` with `homepage_card_slot: "8559569688"`. Preserve the existing two post slots.
6. Commit and deploy; keep **Auto Ads OFF**. Do not create separate ad units for each appearance.

## Exact implementation
- Each HTML homepage/page/N feed places the same ad unit **after the 6th and 12th posts** (12 posts per page).
- A one-column mobile layout and the 2- or 3-column desktop CSS grid give the ad the **same 4:5 tile dimensions** as every photo card.
- Infinite scrolling appends new tiles after 18, 24, 30, etc. posts and explicitly initializes dynamically added AdSense units.
- The homepage slot is now configured: a labelled 4:5 ad tile appears after each six photography cards, including cards added by infinite scrolling.
- The ad creative is fully visible within its standard-size slot, centered in the 4:5 tile. Unused space belongs to the neutral ad-card background instead of a clipped or stretched creative.
- **Policy note:** the homepage features links and some thumbnail covers for adult photography. Using AdSense adjacent to that content can create policy risk; review the homepage content and the AdSense Policy center before monetizing this slot.
- Auto Ads and Auto optimise remain account-level OFF per the owner's screenshot, not modified by this change.
