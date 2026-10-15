# byLYNCH privacy and rights remediation — 15 October 2026

This tracks F04, F06, F07 and F09. It does **not** certify privacy-law or AdSense compliance.

## F04 — Advertising and consent
- The site-managed AdSense script is no longer inserted unconditionally.
- It loads on eligible pages only after an affirmative *local* advertising preference; an initial visitor or one who declines does not trigger the site's AdSense script.
- Consent preference is stored under localStorage key `bylynch-ad-choice-v1`, with a "Privacy choices" footer button for later updates.
- Flagged mature post pages still omit the publisher meta tag and block the AdSense script regardless of the preference.
- **Important:** This is an interim preference widget, **not** a certified IAB TCF CMP. It sends no TCF consent string and does not solve every jurisdiction's requirements.
- **Owner action (AdSense dashboard):** Privacy & messaging → European regulations → Create message → select bylynch.com → configure vendors, languages and an accessible decline option → set Privacy Policy URL `https://bylynch.com/privacy/` → publish. Google offers a certified CMP through Privacy & messaging.
- Coordinate Google CMP integration with the interim local preference layer. The opt-in-gated script can also affect AdSense verification. Do not treat the local panel as a replacement for a certified CMP.
- Test actual network requests and cookies in fresh / declined / allowed browsers in relevant jurisdictions; check account Auto Ads exclusions and site approval.

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
- With browser dev tools, confirm no AdSense request on first visit, after decline, or on any flagged gallery even after an allow choice.
- Confirm that choosing allow triggers the script on a permitted route and that returning to decline reloads the page.
- Check no YouTube/SoundCloud player requests occur before a specific player is clicked.
- Confirm archived comments remain readable, their content is HTML escaped, and review links open Contact #privacy-request.
- Check that local request preparation copies text and **never sends it** automatically.
