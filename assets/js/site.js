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
  function initPhotoLightbox(){
    if(document.querySelector('.photo-lightbox'))return;

    const box=document.createElement('div');
    box.className='photo-lightbox';
    box.setAttribute('role','dialog');
    box.setAttribute('aria-modal','true');
    box.setAttribute('aria-label','Photo viewer');
    box.innerHTML=
      '<div class="photo-lightbox-counter"></div>'+
      '<button class="photo-lightbox-close" type="button" aria-label="Close">×</button>'+
      '<button class="photo-lightbox-prev" type="button" aria-label="Previous photo">‹</button>'+
      '<div class="photo-lightbox-stage"><img class="photo-lightbox-image" alt=""><div class="photo-lightbox-caption"></div></div>'+
      '<button class="photo-lightbox-next" type="button" aria-label="Next photo">›</button>';
    document.body.appendChild(box);

    const view=box.querySelector('.photo-lightbox-image');
    const caption=box.querySelector('.photo-lightbox-caption');
    const counter=box.querySelector('.photo-lightbox-counter');
    const prev=box.querySelector('.photo-lightbox-prev');
    const next=box.querySelector('.photo-lightbox-next');
    const close=box.querySelector('.photo-lightbox-close');
    let images=[],index=0,touchX=null;

    const currentImages=()=>[...document.querySelectorAll('.single .entry-content img')].filter(img=>img.src);
    const render=()=>{
      if(!images.length)return;
      const img=images[index];
      view.src=img.currentSrc||img.src;
      view.alt=img.alt||'';
      const cap=img.closest('figure')?.querySelector('figcaption')?.textContent?.trim()||'';
      caption.textContent=cap;
      caption.style.display=cap?'block':'none';
      counter.textContent=(index+1)+' / '+images.length;
      const multiple=images.length>1;
      prev.style.display=multiple?'block':'none';
      next.style.display=multiple?'block':'none';
    };
    const open=(img)=>{
      images=currentImages();
      index=Math.max(0,images.indexOf(img));
      render();
      box.classList.add('is-open');
      document.body.classList.add('lightbox-open');
      close.focus();
    };
    const hide=()=>{
      box.classList.remove('is-open');
      document.body.classList.remove('lightbox-open');
      view.removeAttribute('src');
    };
    const move=(dir)=>{
      if(!images.length)return;
      index=(index+dir+images.length)%images.length;
      render();
    };

    document.addEventListener('click',e=>{
      const img=e.target.closest?.('.single .entry-content img');
      if(!img)return;
      e.preventDefault();
      open(img);
    });
    close.addEventListener('click',hide);
    prev.addEventListener('click',()=>move(-1));
    next.addEventListener('click',()=>move(1));
    box.addEventListener('click',e=>{if(e.target===box)hide();});
    box.addEventListener('touchstart',e=>{touchX=e.changedTouches[0]?.clientX??null;},{passive:true});
    box.addEventListener('touchend',e=>{
      if(touchX===null)return;
      const dx=(e.changedTouches[0]?.clientX??touchX)-touchX;
      if(Math.abs(dx)>55)move(dx>0?-1:1);
      touchX=null;
    },{passive:true});
    document.addEventListener('keydown',e=>{
      if(!box.classList.contains('is-open'))return;
      if(e.key==='Escape')hide();
      else if(e.key==='ArrowLeft')move(-1);
      else if(e.key==='ArrowRight')move(1);
    });
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
  window.addEventListener('load',()=>{styleCards();cleanImageLists();initBkMasonry();initOlderPosts();initPhotoLightbox();});
  window.addEventListener('resize',()=>{clearTimeout(window.__gazetteResize);window.__gazetteResize=setTimeout(()=>{styleCards();layoutBkMasonry();},120);});
})();