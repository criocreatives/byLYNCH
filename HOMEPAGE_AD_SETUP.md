# byLYNCH — Homepage grid ad (one after six posts)

## AdSense unit to create
1. AdSense → Ads → **By ad unit** → **Display ads**.
2. Name: `byLYNCH — Homepage Grid (6 Cards)`.
3. Ad size: **Responsive** (not Fixed). The **Square** layout preview is closest to the site's 4:5 portrait tiles; the preview does not fix the served creative's dimensions.
4. Save and get code. Send the numeric **data-ad-slot** ID from that code.
5. Set it in `_data/manual_ads.yml` as `homepage_card_slot: "GOOGLE_PROVIDED_NUMERIC_ID"`, preserving the existing two post slots.
6. Commit and deploy; keep **Auto Ads OFF**. Do not create separate ad units for each appearance.

## Exact implementation
- Each HTML homepage/page/N feed places the same ad unit **after the 6th and 12th posts** (12 posts per page).
- A one-column mobile layout and the 2- or 3-column desktop CSS grid give the ad the **same 4:5 tile dimensions** as every photo card.
- Infinite scrolling appends new tiles after 18, 24, 30, etc. posts and explicitly initializes dynamically added AdSense units.
- When `homepage_card_slot` is empty, the source generates **no placeholder tiles**, so deployment is visually unchanged.
- The creative itself is selected by Google; its exact proportions may differ within the reserved card-shaped slot.
- **Policy note:** the homepage features links and some thumbnail covers for adult photography. Using AdSense adjacent to that content can create policy risk; review the homepage content and the AdSense Policy center before monetizing this slot.
- Auto Ads and Auto optimise remain account-level OFF per the owner's screenshot, not modified by this change.
