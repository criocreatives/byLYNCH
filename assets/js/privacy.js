/* byLYNCH privacy controls.
   Interim advertising preference: NOT a Google-certified or IAB TCF CMP. */
(function(){
  'use strict';
  const KEY='bylynch-ad-choice-v1';
  let choice=null, adLoaded=false;
  try{choice=localStorage.getItem(KEY);}catch(e){}
  if(choice!=='allow'&&choice!=='decline')choice=null;
  function loadAds(){
    if(choice!=='allow'||adLoaded)return;
    const meta=document.querySelector('meta[name="google-adsense-account"]');
    // No publisher meta on classified galleries: advertising stays disabled there.
    if(!meta||meta.content!=='ca-pub-4888519100229596')return;
    adLoaded=true;
    const tag=document.createElement('script');
    tag.async=true;
    tag.crossOrigin='anonymous';
    tag.src='https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='+encodeURIComponent(meta.content);
    document.head.appendChild(tag);
  }
  if(choice==='allow')loadAds();
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
    const panel=document.createElement('section');
    panel.className='bylynch-privacy-panel';
    panel.hidden=true;
    panel.setAttribute('aria-labelledby','bylynch-privacy-title');
    panel.innerHTML='<div class="privacy-panel-inner"><div><p class="privacy-panel-eyebrow">BY LYNCH / PRIVACY</p>'+
      '<h2 id="bylynch-privacy-title">Your privacy choices</h2>'+
      '<p>Optional Google advertising is off until you allow it. Audio and video players load only when you choose to play them. You can change the advertising choice at any time.</p>'+
      '<p class="privacy-panel-details">This local preference is not a certified consent management platform. <a href="/cookies/">Read Cookies &amp; Tracking</a>.</p></div>'+
      '<div class="privacy-panel-actions"><button type="button" data-ads-choice="decline">Decline optional ads</button>'+
      '<button type="button" class="privacy-allow-button" data-ads-choice="allow">Allow advertising</button></div></div>';
    document.body.appendChild(panel);
    const show=(focus)=>{panel.hidden=false;if(focus)panel.querySelector('[data-ads-choice="decline"]').focus();};
    panel.querySelectorAll('[data-ads-choice]').forEach(b=>{
      b.addEventListener('click',()=>{
        const alreadyLoaded=adLoaded;
        choice=b.dataset.adsChoice;
        try{localStorage.setItem(KEY,choice);}catch(e){}
        panel.hidden=true;
        if(choice==='allow')loadAds();
        if(choice==='decline'&&alreadyLoaded)location.reload();
      });
    });
    document.querySelectorAll('[data-privacy-choices]').forEach(button=>button.addEventListener('click',()=>show(true)));
    if(choice===null)show(false);
    loadMediaOnDemand();
    initRequestPreparer();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
  else init();
})();