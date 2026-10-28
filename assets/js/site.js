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
  // Backstop for homepage/archive card badges, including infinite-scroll posts.
  // Match the card's actual link slug if Jekyll's server-rendered badge is absent.
  function ensureGalleryRatingBadges(){
    const source=document.getElementById('bylynch-rating-slugs');
    if(!source)return;
    let slugs;
    try{slugs=new Set(JSON.parse(source.textContent||'[]'));}catch(error){return;}
    if(!slugs.size)return;
    document.querySelectorAll('.blog .hentry.format-gallery.has-post-thumbnail').forEach(card=>{
      const link=card.querySelector('.entry-title a[href]');
      if(!link)return;
      let slug;
      try{slug=new URL(link.getAttribute('href'),document.baseURI).pathname.split('/').filter(Boolean).pop();}
      catch(error){return;}
      if(!slugs.has(slug)||card.querySelector('.content-rating-badge'))return;
      const badge=document.createElement('span');
      badge.className='content-rating-badge';
      badge.setAttribute('role','img');
      badge.setAttribute('aria-label','Mature content: nudity');
      badge.title='Mature content';
      badge.textContent='E';
      card.insertBefore(badge,card.firstChild);
    });
  }
  function styleCards(){
    ensureGalleryRatingBadges();
    document.querySelectorAll('.blog .hentry.format-gallery.has-post-thumbnail').forEach(card=>{
      if(getComputedStyle(card).display==='none')return;
      const meta=card.querySelector('.entry-meta'), thumb=card.querySelector('.post-thumbnail');
      if(!thumb)return;
      const bg=thumb.dataset.bg;
      if(bg&&!thumb.querySelector('.post-thumbnail-image'))thumb.style.backgroundImage='url("'+bg+'")';
      const top=meta?(meta.offsetHeight+15):0;
      thumb.style.top=top+'px';
      thumb.style.height=Math.max(0,card.offsetHeight-top)+'px';
      if(meta){
        const a=meta.querySelector('.cat-links'),b=meta.querySelector('.comments-link');
        card.classList.toggle('long-meta',!!(a&&b&&a.offsetWidth+b.offsetWidth>=meta.offsetWidth));
      }
    });
  }
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
  function cleanImageLists(){
    document.querySelectorAll('.entry-content li').forEach(li=>{if(li.querySelector('img')){li.style.listStyle='none';li.style.marginLeft='0';li.style.paddingLeft='0';const p=li.parentElement;if(p){p.classList.add('image-list');}}});
  }
  function normalizePostTextNodes(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;

    const inlineTags=new Set(['A','ABBR','B','BR','CITE','CODE','DEL','EM','I','INS','MARK','Q','S','SMALL','SPAN','STRONG','SUB','SUP','U']);
    let paragraph=null;

    const startParagraph=(before)=>{
      if(paragraph)return paragraph;
      paragraph=document.createElement('p');
      grid.insertBefore(paragraph,before);
      return paragraph;
    };

    [...grid.childNodes].forEach(node=>{
      if(node.nodeType===Node.TEXT_NODE){
        if(!node.textContent.replace(/\u00a0/g,' ').trim()){
          if(paragraph)paragraph.appendChild(document.createTextNode(' '));
          node.remove();
          return;
        }
        startParagraph(node).appendChild(node);
        return;
      }

      if(node.nodeType!==Node.ELEMENT_NODE)return;

      if(node.tagName==='HR'){
        node.remove();
        paragraph=null;
        return;
      }

      if(inlineTags.has(node.tagName)){
        startParagraph(node).appendChild(node);
        return;
      }

      paragraph=null;
    });

    [...grid.querySelectorAll(':scope > p')].forEach(p=>{
      const plain=p.textContent.replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim();
      if(!plain || /^[,;:.!?'"“”‘’\-–—…]+(?:\s+(?:and|or))?$/i.test(plain))p.remove();
    });
  }
  function normalizeNestedPostGalleries(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;
    [...grid.children].forEach(child=>{
      const imgs=[...child.querySelectorAll('img')];

      if(!imgs.length && !child.textContent.trim() &&
         child.matches('.wp-gallery,.wp-block-gallery,.wp-block-image,h1,h2,h3,h4,h5,h6,p')){
        child.remove();
        return;
      }

      if(imgs.length<2)return;
      const galleryLike=
        child.matches('.wp-block-gallery,.wp-block-coblocks-gallery-stacked,.gallery,.wp-gallery,[class*="gallery"]') ||
        !!child.querySelector('.wp-block-gallery,.coblocks-gallery,.gallery,.wp-gallery,[class*="gallery"]');
      const imagesOnly=!child.textContent.trim();
      if(!galleryLike && !imagesOnly)return;

      const frag=document.createDocumentFragment();
      imgs.forEach(img=>{
        const closest=img.closest('figure');
        let item;
        if(closest && closest!==child && child.contains(closest) && closest.querySelectorAll('img').length===1){
          item=closest.cloneNode(true);
        }else{
          item=document.createElement('figure');
          item.className='wp-block-image';
          item.appendChild(img.cloneNode(true));
        }
        item.classList.add('masonry-item');
        item.removeAttribute('style');
        frag.appendChild(item);
      });
      child.replaceWith(frag);
    });
  }
  function normalizeStandalonePostImages(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;
    [...grid.children].forEach(child=>{
      if(child.tagName==='IMG'){
        const figure=document.createElement('figure');
        figure.className='wp-block-image masonry-item';
        child.replaceWith(figure);
        figure.appendChild(child);
      }else if(child.tagName==='P'&&child.querySelectorAll('img').length===1
          &&!child.textContent.trim()&&!child.querySelector('video,iframe,figcaption')){
        const img=child.querySelector('img');
        const figure=document.createElement('figure');
        figure.className='wp-block-image masonry-item';
        child.replaceWith(figure);
        figure.appendChild(img);
      }
    });
  }
  function markFullWidthEmbeds(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;
    [...grid.children].forEach(child=>{
      const frame=child.matches('iframe[src*="youtube.com/embed"],iframe[src*="youtube-nocookie.com/embed"]')
        ? child
        : child.querySelector('iframe[src*="youtube.com/embed"],iframe[src*="youtube-nocookie.com/embed"]');
      if(frame || child.matches('.soundcloud-embed'))child.classList.add('full-width-embed');
    });
  }
  function bkColumnCount(){
    const w=window.innerWidth;
    if(w>=900)return 3;
    if(w>=600)return 2;
    return 1;
  }
  function layoutBkMasonry(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;
    const gap=10;
    const cols=bkColumnCount();
    const items=[...grid.children].filter(el=>getComputedStyle(el).display!=='none');
    const total=grid.clientWidth;
    const colWidth=(total-gap*(cols-1))/cols;
    const heights=new Array(cols).fill(0);

    let normalIndex=0;
    items.forEach(item=>{
      const full=item.classList.contains('full-width-embed');
      if(full){
        const top=Math.max(0,...heights);
        item.style.position='absolute';
        item.style.width=total+'px';
        item.style.left='0px';
        item.style.top=top+'px';
        item.style.gridColumn='';
        item.style.gridRow='';
        const h=item.getBoundingClientRect().height;
        const next=top+h+gap;
        heights.fill(next);
        normalIndex=0;
        return;
      }

      const col=normalIndex%cols;
      normalIndex++;
      item.style.position='absolute';
      item.style.width=colWidth+'px';
      item.style.left=(col*(colWidth+gap))+'px';
      item.style.top=heights[col]+'px';
      item.style.gridColumn='';
      item.style.gridRow='';
      const h=item.getBoundingClientRect().height;
      heights[col]+=h+gap;
    });

    grid.style.height=Math.max(0,...heights)-gap+'px';
  }
  function initBkMasonry(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;
    normalizePostTextNodes();
    normalizeNestedPostGalleries();
    normalizeStandalonePostImages();
    markFullWidthEmbeds();
    grid.classList.add('masonry-initialized');
    const images=[...grid.querySelectorAll('img')];
    let layoutFrame=0;
    const scheduleLayout=()=>{
      if(layoutFrame)return;
      layoutFrame=requestAnimationFrame(()=>{
        layoutFrame=0;
        layoutBkMasonry();
      });
    };
    images.forEach((img,index)=>{
      img.decoding='async';
      // Get the first few photos on screen promptly, without loading the whole gallery.
      if(index<3)img.loading='eager';
      else if(!img.hasAttribute('loading'))img.loading='lazy';
      const markLoaded=()=>{
        img.classList.add('lazy-loaded');
        scheduleLayout();
      };
      if(img.complete&&img.naturalWidth)markLoaded();
      else if(img.complete)img.addEventListener('error',scheduleLayout,{once:true});
      else{
        img.addEventListener('load',markLoaded,{once:true});
        img.addEventListener('error',scheduleLayout,{once:true});
      }
    });
    // Explicitly activate near-viewport images in the absolute masonry layout.
    // The browser's native lazy-loading heuristic can otherwise leave blanks.
    if('IntersectionObserver' in window){
      const near=new IntersectionObserver(entries=>{
        entries.forEach(entry=>{
          if(!entry.isIntersecting)return;
          const img=entry.target;
          if(img.loading==='lazy')img.loading='eager';
          near.unobserve(img);
        });
      },{rootMargin:'1100px 0px'});
      images.slice(3).forEach(img=>{if(img.loading==='lazy')near.observe(img);});
    }
    if('ResizeObserver' in window){
      const resize=new ResizeObserver(scheduleLayout);
      [...grid.children].forEach(child=>resize.observe(child));
    }
    requestAnimationFrame(()=>requestAnimationFrame(layoutBkMasonry));
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
    if(!/^\d+$/.test(slot))return null;
    const tile=document.createElement('aside');
    tile.className='bylynch-home-grid-ad';
    tile.dataset.homeGridAd='';
    tile.setAttribute('aria-label','Advertisement');
    const label=document.createElement('div');
    label.className='bylynch-home-grid-ad-label';
    label.setAttribute('aria-hidden','true');
    label.textContent='ADVERTISEMENT';
    const unit=document.createElement('ins');
    unit.className='adsbygoogle bylynch-home-grid-ad-unit';
    unit.style.display='block';
    unit.style.width='200px';
    unit.style.height='200px';
    unit.dataset.adClient='ca-pub-4888519100229596';
    unit.dataset.adSlot=slot;
    tile.append(label,unit);
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
          styleCards();
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
  window.addEventListener('load',()=>{initArchiveFilter();styleCards();markClippedExcerpts();cleanImageLists();initBkMasonry();activateHomeGridAds();activateManualPostAds();initOlderPosts();});
  window.addEventListener('resize',()=>{clearTimeout(window.__gazetteResize);window.__gazetteResize=setTimeout(()=>{styleCards();markClippedExcerpts();layoutBkMasonry();},180);});
})();