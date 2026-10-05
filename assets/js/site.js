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
    li.appendChild(b);
    b.addEventListener('click',e=>{e.preventDefault();const sub=li.querySelector('.sub-menu');if(!sub)return;const on=sub.classList.toggle('toggled');b.classList.toggle('toggled',on);b.setAttribute('aria-expanded',on?'true':'false');});
  });
  function styleCards(){
    document.querySelectorAll('.blog .hentry.format-gallery.has-post-thumbnail').forEach(card=>{
      const meta=card.querySelector('.entry-meta'), thumb=card.querySelector('.post-thumbnail');
      if(!thumb)return;
      const bg=thumb.dataset.bg;if(bg)thumb.style.backgroundImage='url("'+bg+'")';
      const top=meta?(meta.offsetHeight+15):0;
      thumb.style.top=top+'px';
      thumb.style.height=Math.max(0,card.offsetHeight-top)+'px';
      if(meta){
        const a=meta.querySelector('.cat-links'),b=meta.querySelector('.comments-link');
        card.classList.toggle('long-meta',!!(a&&b&&a.offsetWidth+b.offsetWidth>=meta.offsetWidth));
      }
    });
  }
  function cleanImageLists(){
    document.querySelectorAll('.entry-content li').forEach(li=>{if(li.querySelector('img')){li.style.listStyle='none';li.style.marginLeft='0';li.style.paddingLeft='0';const p=li.parentElement;if(p){p.classList.add('image-list');}}});
  }
  function normalizePostTextNodes(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;
    [...grid.childNodes].forEach(node=>{
      if(node.nodeType!==Node.TEXT_NODE)return;
      const text=node.textContent.replace(/\s+/g,' ').trim();
      if(!text){node.remove();return;}
      const p=document.createElement('p');
      p.textContent=text;
      node.replaceWith(p);
    });
    grid.querySelectorAll(':scope > hr').forEach(hr=>hr.remove());
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

    items.forEach((item,i)=>{
      const col=i%cols;
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
    grid.querySelectorAll('img').forEach(img=>{
      const markLoaded=()=>{
        img.classList.add('lazy-loaded');
        layoutBkMasonry();
      };
      if(img.complete && img.naturalWidth){
        markLoaded();
      }else{
        img.addEventListener('load',markLoaded,{once:true});
      }
    });
    requestAnimationFrame(()=>requestAnimationFrame(layoutBkMasonry));
  }
  function initOlderPosts(){
    const button=document.querySelector('.older-posts-button');
    if(!button)return;
    button.addEventListener('click',async()=>{
      const next=button.dataset.nextUrl;
      if(!next)return;
      const original=button.textContent;
      button.disabled=true;
      button.textContent='LOADING…';
      try{
        const res=await fetch(next,{credentials:'same-origin'});
        if(!res.ok)throw new Error('Could not load older posts');
        const html=await res.text();
        const doc=new DOMParser().parseFromString(html,'text/html');
        const incoming=[...doc.querySelectorAll('.blog .site-main > .hentry')];
        const target=document.querySelector('.blog .site-main');
        if(target)incoming.forEach(card=>target.appendChild(document.importNode(card,true)));
        const nextButton=doc.querySelector('.older-posts-button');
        if(nextButton&&nextButton.dataset.nextUrl){
          button.dataset.nextUrl=nextButton.dataset.nextUrl;
          button.disabled=false;
          button.textContent=original;
        }else{
          button.closest('.older-posts-wrap')?.remove();
        }
        requestAnimationFrame(()=>requestAnimationFrame(styleCards));
      }catch(err){
        button.disabled=false;
        button.textContent=original;
        console.error(err);
      }
    });
  }
  const hero=document.querySelector('[data-entry-hero] [data-featured-image]');
  if(hero){
    hero.addEventListener('error',()=>{const first=document.querySelector('.entry-content img');if(first&&hero.src!==first.src)hero.src=first.src;});
    if(!hero.getAttribute('src')){const first=document.querySelector('.entry-content img');if(first)hero.src=first.src;}
  }
  window.addEventListener('load',()=>{styleCards();cleanImageLists();initBkMasonry();initOlderPosts();});
  window.addEventListener('resize',()=>{clearTimeout(window.__gazetteResize);window.__gazetteResize=setTimeout(()=>{styleCards();layoutBkMasonry();},120);});
})();