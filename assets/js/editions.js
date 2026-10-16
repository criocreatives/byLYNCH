(() => {
  const form = document.getElementById('editions-enquiry');
  const output = document.getElementById('editions-copy');
  const status = document.getElementById('editions-enquiry-status');
  if (!form || !output || !status) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const type = form.elements.category.value;
    const details = form.elements.details.value.trim();
    if (!details) { status.textContent = 'Add your image URL and proposed use.'; return; }
    const message = 'byLYNCH enquiry\nType: ' + type + '\nDetails: ' + details +
      '\n\nPlease let me know about availability, required permissions, terms and pricing.';
    output.value = message;
    output.hidden = false;
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('clipboard unavailable');
      await navigator.clipboard.writeText(message);
      status.textContent = 'Copied. Send this message via the @lebosslynch contact link.';
    } catch (_) {
      output.focus(); output.select();
      status.textContent = 'Select and copy the prepared message, then send it via the contact link.';
    }
  });
})();
