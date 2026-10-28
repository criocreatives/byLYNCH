/* byLYNCH: post-only photo viewer, retaining gallery image order. */
(function(){
  function initPhotoLightbox(){
    if(document.querySelector('.photo-lightbox')){window.bylynchRefreshPhotoLightbox?.();return;}

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
    let images=[],index=0,touchX=null,returnFocus=null;
    const gallerySelector='.single .entry-content img';
    // Only gallery imagery is interactive. Keep the image itself unchanged.
    const makeAccessible=()=>{
      document.querySelectorAll(gallerySelector).forEach(img=>{
        if(img.dataset.lightboxReady)return;
        img.dataset.lightboxReady='true';
        if(!img.hasAttribute('tabindex'))img.setAttribute('tabindex','0');
        img.setAttribute('role','button');
        img.setAttribute('aria-haspopup','dialog');
        img.setAttribute('aria-label',(img.alt||'Gallery photograph')+' — open photo viewer');
      });
    };
    window.bylynchRefreshPhotoLightbox=makeAccessible;
    makeAccessible();

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
      returnFocus=document.activeElement;
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
      if(returnFocus && returnFocus.isConnected && typeof returnFocus.focus==='function')returnFocus.focus();
      returnFocus=null;
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
      if(!box.classList.contains('is-open')){
        if((e.key==='Enter'||e.key===' ') &&
           e.target?.matches?.(gallerySelector)){
          e.preventDefault();open(e.target);
        }
        return;
      }
      if(e.key==='Escape'){e.preventDefault();hide();}
      else if(e.key==='ArrowLeft'){e.preventDefault();move(-1);}
      else if(e.key==='ArrowRight'){e.preventDefault();move(1);}
      else if(e.key==='Tab'){
        const focusable=[close,prev,next].filter(el=>getComputedStyle(el).display!=='none');
        if(!focusable.length)return;
        const i=focusable.indexOf(document.activeElement);
        if(e.shiftKey && (i<=0)){e.preventDefault();focusable[focusable.length-1].focus();}
        else if(!e.shiftKey && (i<0||i===focusable.length-1)){e.preventDefault();focusable[0].focus();}
      }
    });
  }
  window.bylynchInitPhotoLightbox=initPhotoLightbox;
  window.addEventListener('load',initPhotoLightbox);
})();
