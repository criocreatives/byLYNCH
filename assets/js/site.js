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
      const top=(meta?meta.offsetHeight:0)+15;
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
  const hero=document.querySelector('[data-entry-hero] [data-featured-image]');
  if(hero){
    hero.addEventListener('error',()=>{const first=document.querySelector('.entry-content img');if(first&&hero.src!==first.src)hero.src=first.src;});
    if(!hero.getAttribute('src')){const first=document.querySelector('.entry-content img');if(first)hero.src=first.src;}
  }
  window.addEventListener('load',()=>{styleCards();cleanImageLists();});
  window.addEventListener('resize',()=>{clearTimeout(window.__gazetteResize);window.__gazetteResize=setTimeout(styleCards,120);});
})();