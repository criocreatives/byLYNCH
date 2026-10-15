# byLYNCH privacy and rights remediation — 15 October 2026

This tracks F04, F06, F07 and F09. It does **not** certify privacy-law or AdSense compliance.

## F04 — Advertising and consent (custom banner removed by owner request)
- The local byLYNCH consent/opt-in panel and footer "Privacy choices" button were removed on 15 October 2026.
- On **unflagged** pages, the original shared AdSense publisher script now loads directly again. This is a technical revert, **not** a compliance determination.
- Nine mature galleries remain on the ad-exclusion list; they omit both the publisher meta and script.
- The site's localStorage key `bylynch-ad-choice-v1` is no longer read or written. Old stored values may remain in a visitor's browser until cleared, but have no effect.
- **Outstanding / material:** In AdSense → Privacy & messaging, configure and publish a Google-certified IAB TCF-integrated CMP for applicable personalized-ad traffic in the EEA, UK and Switzerland. Confirm other applicable regional consent obligations, vendor settings, and Google Auto Ads page exclusions.
- Test real browser network behavior on unflagged pages and the nine excluded galleries. No website-wide custom opt-in banner is presently active.
- Removing the custom panel does not relieve the publisher from any legal or Google-policy consent requirement.

## F06 — Third-party media and fonts
- The Jekyll post layout defers eight known YouTube iframe sources and one SoundCloud iframe source until individual click-to-load activation.
- Original article bodies, photographs, cover mappings, and captions were not changed.
- Google Fonts remains requested by CSS. Review suitable licensed self-hosted Lato assets to eliminate the third-party font request without unapproved visual changes.
- Verify embeds and players in a desktop and mobile browser, including no-JavaScript behavior; their content must remain available on click, not automatically loaded.

## F07 — Archived comments
- Historic comments are clearly labeled and linked to a review request procedure.
- Comment body text is HTML-escaped, existing comments and attribution remain intact, and untrusted author-site links are marked nofollow/ugc.
- Future correction/removal decisions require case-by-case review and a private contact channel, not automatic deletion. Verify original-comment HTML formatting for any regressions.

## F09 — Contact intake
- The existing Contact page now prepares a privacy or rights inquiry entirely in the visitor's browser, ready for them to copy and send via the established public Instagram contact.
- No message is submitted, uploaded or saved by the site. Do not solicit identity documents or intimate evidence over social DMs.
- **Still required:** A verified and monitored private byLYNCH inbox (or encrypted submission endpoint), plus an escalation process for sensitive verification, requests and records. Do not invent or publish unverified addresses.

## Verification
- Check GitHub Pages build status and current deployed HTML.
- With browser dev tools, confirm AdSense is loaded on unflagged pages and omitted on the nine flagged galleries.
- Confirm the custom pop-up and footer "Privacy choices" button no longer appear; validate regional certified CMP behavior separately when configured.
- Check no YouTube/SoundCloud player requests occur before a specific player is clicked.
- Confirm archived comments remain readable, their content is HTML escaped, and review links open Contact #privacy-request.
- Check that local request preparation copies text and **never sends it** automatically.
