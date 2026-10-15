/* byLYNCH on-demand third-party media and browser-only request preparation.
   This script does not display a sitewide privacy/consent banner. */
(function(){
  'use strict';
  function loadMediaOnDemand(){
    document.querySelectorAll('iframe[data-embed-src]').forEach(frame=>{
      let url;
      try{url=new URL(frame.getAttribute('data-embed-src'),document.baseURI);}catch(e){return;}
      const youtube=['www.youtube.com','youtube.com','www.youtube-nocookie.com'].includes(url.hostname);
      const soundcloud=url.hostname==='w.soundcloud.com';
      if(!youtube&&!soundcloud)return;
      const provider=youtube?'YouTube':'SoundCloud';
      const gate=document.createElement('div');
      gate.className='privacy-media-gate'+(soundcloud?' is-audio':'');
      const title=document.createElement('p');
      title.className='privacy-media-title';
      title.textContent=provider+' media is paused';
      const caption=document.createElement('p');
      caption.className='privacy-media-info';
      caption.textContent='Loading this '+(soundcloud?'audio':'video')+' will connect to '+provider+'.';
      const load=document.createElement('button');
      load.type='button';
      load.className='privacy-media-play';
      load.textContent='Load '+provider+' '+(soundcloud?'audio':'video');
      load.addEventListener('click',()=>{
        frame.removeAttribute('data-embed-src');
        frame.src=url.href;
        gate.replaceWith(frame);
        frame.addEventListener('load',()=>window.dispatchEvent(new Event('resize')),{once:true});
        window.dispatchEvent(new Event('resize'));
      });
      gate.append(title,caption,load);
      frame.replaceWith(gate);
    });
  }
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
    loadMediaOnDemand();
    initRequestPreparer();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
  else init();
})();
