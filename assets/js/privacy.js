/* byLYNCH browser-only contact request preparation.
   Normal third-party media embeds load using their original iframe URLs.
   No consent banner or media click-to-load gate is installed here. */
(function(){
  'use strict';
  function initRequestPreparer(){
    const form=document.getElementById('bylynch-request-preparer');
    if(!form)return;
    const output=document.getElementById('bylynch-request-copy');
    const status=document.getElementById('bylynch-request-status');
    form.addEventListener('submit',async event=>{
      event.preventDefault();
      const kind=form.elements['request_type'].value;
      const page=form.elements['page_url'].value.trim();
      const description=form.elements['request_detail'].value.trim();
      if(!description){status.textContent='Please describe the request first.';return;}
      const message='byLYNCH — '+kind+' request\n'+(page?'Page: '+page+'\n':'')+
        'Request: '+description+'\n\nPlease provide a suitable private channel if additional verification is needed.';
      output.value=message;
      output.hidden=false;
      try{
        if(window.isSecureContext&&navigator.clipboard){
          await navigator.clipboard.writeText(message);
          status.textContent='Request copied. Open Instagram below and paste it into a new message.';
        }else{
          output.focus();output.select();status.textContent='Select and copy the request, then open Instagram below.';
        }
      }catch(e){output.focus();output.select();status.textContent='Select and copy the request, then open Instagram below.';}
    });
  }
  function init(){
    initRequestPreparer();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
  else init();
})();
