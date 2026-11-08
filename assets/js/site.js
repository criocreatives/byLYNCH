(function(){
  const nav=document.getElementById('site-navigation');
  const toggle=nav && nav.querySelector('.menu-toggle');
  if(toggle){
    toggle.addEventListener('click',()=>{
      const on=nav.classList.toggle('toggled');
      toggle.setAttribute('aria-expanded',on?'true':'false');
    });
  }
  document.querySelectorAll('.main-navigation .menu-item-has-children').forEach(li=>{
    const b=document.createElement('button');b.className='dropdown-toggle';b.type='button';b.setAttribute('aria-expanded','false');
    const submenu=li.querySelector('.sub-menu');
    const label=li.querySelector(':scope > a')?.textContent?.trim()||'Menu';
    b.setAttribute('aria-label','Toggle '+label+' submenu');
    if(submenu){
      if(!submenu.id)submenu.id='bylynch-submenu-'+Math.random().toString(36).slice(2,10);
      b.setAttribute('aria-controls',submenu.id);
    }
    li.appendChild(b);
    b.addEventListener('click',e=>{e.preventDefault();const sub=li.querySelector('.sub-menu');if(!sub)return;const on=sub.classList.toggle('toggled');b.classList.toggle('toggled',on);b.setAttribute('aria-expanded',on?'true':'false');});
  });
  function markClippedExcerpts(root=document){
    root.querySelectorAll('.blog .hentry.format-gallery.has-post-thumbnail').forEach(card=>{
      const p=card.querySelector('.card-copy .entry-summary p');
      const copy=card.querySelector('.card-copy');
      if(!p||!copy)return;

      const clone=p.cloneNode(true);
      clone.style.position='absolute';
      clone.style.visibility='hidden';
      clone.style.pointerEvents='none';
      clone.style.display='block';
      clone.style.webkitLineClamp='unset';
      clone.style.overflow='visible';
      clone.style.maxHeight='none';
      clone.style.width=p.clientWidth+'px';
      copy.appendChild(clone);

      const cs=getComputedStyle(p);
      const line=parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.5;
      const clipped=clone.scrollHeight>(line*2+2);
      clone.remove();
      card.classList.toggle('has-clipped-excerpt',clipped);
    });
  }
  function initArchiveFilter(){
    if(!document.body.classList.contains('archive-page'))return;
    const params=new URLSearchParams(location.search);
    const cat=(params.get('cat')||'').trim().toLowerCase();
    const tag=(params.get('tag')||'').trim().toLowerCase();
    document.querySelectorAll('.archive-page .site-main > .hentry').forEach(card=>{
      const cats=(card.dataset.categories||'').split('||').map(x=>x.trim().toLowerCase()).filter(Boolean);
      const tags=(card.dataset.tags||'').split('||').map(x=>x.trim().toLowerCase()).filter(Boolean);
      const matchCat=!cat||cats.includes(cat);
      const matchTag=!tag||tags.includes(tag);
      card.style.display=(matchCat&&matchTag)?'block':'none';
    });
  }
  // Google-supported exact creative sizes. Select one before requesting each ad.
  // Never crop, hide or resize a creative after it has been served.
  function requestSizedAd(unit,availableWidth,type){
    if(!unit||unit.dataset.adInitialized==='1'||unit.hasAttribute('data-adsbygoogle-status'))return;
    const available=Math.floor(availableWidth);
    let size=null;
    if(type==='home'){
      const safe=available-24;
      if(safe>=300)size=[300,250];
      else if(safe>=250)size=[250,250];
      else if(safe>=200)size=[200,200];
      else if(safe>=180)size=[180,150];
    }else if(type==='metadata'){
      if(available>=320)size=[320,100];
      else if(available>=234)size=[234,60];
    }else if(type==='after-gallery'){
      if(available>=748)size=[728,90];
      else if(available>=488)size=[468,60];
      else if(available>=320)size=[300,250];
      else if(available>=270)size=[250,250];
      else if(available>=220)size=[200,200];
    }
    if(!size)return;
    unit.style.display='block';
    unit.style.width=size[0]+'px';
    unit.style.height=size[1]+'px';
    unit.style.margin='0 auto';
    unit.removeAttribute('data-ad-format');
    unit.removeAttribute('data-full-width-responsive');
    unit.dataset.adInitialized='1';
    try{(window.adsbygoogle=window.adsbygoogle||[]).push({});}
    catch(error){
      delete unit.dataset.adInitialized;
      console.error('byLYNCH ad request failed',error);
    }
  }
  function createHomeGridAd(slot){
    const template=document.getElementById('home-grid-ad-template');
    const tile=template?.content.firstElementChild?.cloneNode(true);
    if(!tile||tile.querySelector('ins')?.dataset.adSlot!==slot)return null;
    return tile;
  }
  function activateHomeGridAds(){
    document.querySelectorAll('[data-post-feed] > [data-home-grid-ad]').forEach(tile=>{
      const unit=tile.querySelector('ins.adsbygoogle');
      requestSizedAd(unit,tile.getBoundingClientRect().width,'home');
    });
  }
  function activateManualPostAds(){
    document.querySelectorAll('.bylynch-manual-ad').forEach(box=>{
      const unit=box.querySelector('ins.adsbygoogle');
      const style=getComputedStyle(box);
      const width=box.clientWidth-(parseFloat(style.paddingLeft)||0)-(parseFloat(style.paddingRight)||0);
      const type=box.classList.contains('bylynch-manual-ad--metadata')?'metadata':'after-gallery';
      requestSizedAd(unit,width,type);
    });
  }
  function initOlderPosts(){
    const feed=document.querySelector('[data-post-feed]');
    const wrap=document.querySelector('.older-posts-wrap');
    const link=wrap?.querySelector('.older-posts-link');
    const status=wrap?.querySelector('.older-posts-status');
    if(!feed||!wrap||!link||!status||!('IntersectionObserver' in window))return;

    let nextUrl=link.href;
    let loading=false;
    const visited=new Set();
    wrap.classList.add('is-auto');

    async function loadMore(){
      if(loading||!nextUrl||wrap.classList.contains('has-error'))return;
      loading=true;
      wrap.classList.add('is-loading');
      status.textContent='LOADING OLDER POSTS…';

      try{
        const url=new URL(nextUrl,location.href);
        if(url.origin!==location.origin||visited.has(url.href))throw new Error('Invalid next page');
        const response=await fetch(url.href,{credentials:'same-origin'});
        if(!response.ok)throw new Error('Older posts could not be retrieved');
        const html=await response.text();
        const doc=new DOMParser().parseFromString(html,'text/html');
        const source=doc.querySelector('[data-post-feed]');
        const incoming=source?[...source.querySelectorAll(':scope > .hentry')]:[];
        if(!incoming.length)throw new Error('Older posts page contains no cards');

        const existing=new Set(
          [...feed.querySelectorAll(':scope > .hentry .entry-title a')]
            .map(a=>new URL(a.getAttribute('href'),location.href).pathname)
        );
        let added=0;
        // Count qualifying photo cards once per batch, not once per append.
        // This preserves the existing ad cadence, including filtered duplicates.
        let totalCards=feed.querySelectorAll(':scope > .hentry.format-gallery.has-post-thumbnail').length;
        incoming.forEach(card=>{
          const href=card.querySelector('.entry-title a')?.getAttribute('href');
          if(!href)return;
          const path=new URL(href,url.href).pathname;
          if(existing.has(path))return;
          existing.add(path);
          feed.appendChild(document.importNode(card,true));
          added++;
          // Count only photographic post cards. Ad tiles never affect the six-card cadence.
          if(card.matches('.hentry.format-gallery.has-post-thumbnail'))totalCards++;
          if(totalCards%6===0&&feed.dataset.homeAdSlot){
            const ad=createHomeGridAd(feed.dataset.homeAdSlot);
            if(ad)feed.appendChild(ad);
          }
        });
        if(!added)throw new Error('No new posts on the next page');
        visited.add(url.href);

        const nextLink=doc.querySelector('.older-posts-link');
        nextUrl=nextLink?new URL(nextLink.getAttribute('href'),url.href).href:null;
        if(nextUrl){
          link.href=nextUrl;
        }else{
          observer.disconnect();
          wrap.remove();
        }
        requestAnimationFrame(()=>requestAnimationFrame(()=>{
          markClippedExcerpts();
          activateHomeGridAds();
          if(nextUrl&&wrap.getBoundingClientRect().top<window.innerHeight+600)loadMore();
        }));
      }catch(error){
        console.error('Could not load older posts:',error);
        observer.disconnect();
        wrap.classList.add('has-error');
        status.textContent='Unable to load automatically. Use the link below to continue.';
      }finally{
        loading=false;
        wrap.classList.remove('is-loading');
        if(!wrap.classList.contains('has-error'))status.textContent='';
      }
    }

    const observer=new IntersectionObserver(entries=>{
      if(entries.some(entry=>entry.isIntersecting))loadMore();
    },{rootMargin:'600px 0px'});
    observer.observe(wrap);
  }
  const hero=document.querySelector('[data-entry-hero] [data-featured-image]');
  if(hero){
    hero.addEventListener('error',()=>{const first=document.querySelector('.entry-content img');if(first&&hero.src!==first.src)hero.src=first.src;});
    if(!hero.getAttribute('src')){const first=document.querySelector('.entry-content img');if(first)hero.src=first.src;}
  }
  window.addEventListener('load',()=>{initArchiveFilter();markClippedExcerpts();activateHomeGridAds();activateManualPostAds();initOlderPosts();});
  window.addEventListener('resize',()=>{clearTimeout(window.__gazetteResize);window.__gazetteResize=setTimeout(()=>{markClippedExcerpts();},180);});
})();