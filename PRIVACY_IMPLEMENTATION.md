# byLYNCH privacy and rights remediation — 15 October 2026

This tracks F04, F06, F07 and F09. It does **not** certify privacy-law or AdSense compliance.

## F04 — Advertising and consent (custom banner removed by owner request)
- The local byLYNCH consent/opt-in panel and footer "Privacy choices" button were removed on 15 October 2026.
- On **unflagged** pages, the original shared AdSense publisher script now loads directly again. This is a technical revert, **not** a compliance determination.
- Nine mature galleries remain on the ad-exclusion list; they omit both the publisher meta and script.
- The site's localStorage key `bylynch-ad-choice-v1` is no longer read or written. Old stored values may remain in a visitor's browser until cleared, but have no effect.
- **Confirmed by owner screenshot (15 October 2026):** Google AdSense → Privacy & messaging → European regulations lists one English message for `bylynch.com`, with status **Published** and the publish toggle enabled. Google's European consent-management service is used instead of the removed custom site pop-up.
- **Remaining checks:** Review the published message's privacy-policy link, the available consent/refusal/settings choices, participating ad vendors and regional message behavior; verify in a browser located in the EEA, UK or Switzerland. Evaluate any independent analytics/media consent requirements. Publishing a message alone does not prove all regional legal obligations have been met.
- Test real browser network behavior on unflagged pages and the nine excluded galleries. No website-wide custom opt-in banner is presently active.
- Removing the custom panel does not relieve the publisher from any legal or Google-policy consent requirement.

## F06 — Third-party media and fonts (original embeds restored by owner request)
- The earlier click-to-load wrappers for YouTube and SoundCloud were removed on 15 October 2026.
- Posts now use their original YouTube and SoundCloud iframe sources. These embeds can contact the external provider as soon as an article loads, before the visitor presses Play.
- The previously identified eight YouTube embeds and one SoundCloud embed are **not** rewritten or replaced with alternate services. Original posts, photography, captions and links are unchanged.
- Browser-only contact request helper (F09) remains implemented in `assets/js/privacy.js`; it no longer handles media.
- Google Fonts continues to load externally. Review licensed self-hosted Lato files separately if desired.
- Confirm normal iframe presentation on mobile and desktop, and verify actual network and cookie behavior for any applicable privacy/consent obligations.

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
- Confirm the custom pop-up and footer "Privacy choices" button do not appear. Verify the **published** Google European regulations message operates correctly for eligible visitors, and confirm its privacy link and visitor-choice settings.
- Confirm YouTube/SoundCloud players load normally without an intermediary click-to-load prompt; assess third-party requests and disclosures.
- Confirm archived comments remain readable, their content is HTML escaped, and review links open Contact #privacy-request.
- Check that local request preparation copies text and **never sends it** automatically.
