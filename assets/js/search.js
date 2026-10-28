/* byLYNCH: isolated site search; versioned per-build index caching. */
(function(){
  function initSiteSearch(){
    const header=document.querySelector('.site-header');
    const button=document.querySelector('.search-toggle');
    if(!header||!button||header.querySelector('.site-search-panel'))return;

    const panel=document.createElement('div');
    panel.className='site-search-panel';
    panel.innerHTML=
      '<div class="site-search-inner">'+
        '<div class="site-search-form">'+
          '<input class="site-search-input" type="search" placeholder="Search by LYNCH…" aria-label="Search posts">'+
          '<button class="site-search-close" type="button" aria-label="Close search">×</button>'+
        '</div>'+
        '<div class="site-search-results"><div class="site-search-empty">Type to search all posts.</div></div>'+
      '</div>';
    header.appendChild(panel);

    const input=panel.querySelector('.site-search-input');
    const results=panel.querySelector('.site-search-results');
    const close=panel.querySelector('.site-search-close');
    let docs=null,loading=null,timer=null;

    const escHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
    const searchIndex=new URL('search.json',document.querySelector('.site-logo-link')?.href||location.origin+'/');
    const version=document.querySelector('script[data-search-version]')?.dataset.searchVersion;
    if(version)searchIndex.searchParams.set('v',version);
    const searchUrl=searchIndex.href;
    const load=()=>{
      if(docs)return Promise.resolve(docs);
      if(loading)return loading;
      loading=fetch(searchUrl,{cache:'default'})
        .then(r=>{if(!r.ok)throw new Error('Search index unavailable');return r.json();})
        .then(data=>docs=data)
        .finally(()=>loading=null);
      return loading;
    };
    const draw=async()=>{
      const q=input.value.trim().toLowerCase();
      if(!q){results.innerHTML='<div class="site-search-empty">Type to search all posts.</div>';return;}
      results.innerHTML='<div class="site-search-empty">Searching…</div>';
      try{
        const data=await load();
        const terms=q.split(/\s+/).filter(Boolean);
        const matches=data.filter(d=>{
          const hay=[d.title,d.excerpt,d.text,(d.categories||[]).join(' '),(d.tags||[]).join(' ')].join(' ').toLowerCase();
          return terms.every(t=>hay.includes(t));
        }).slice(0,10);
        if(!matches.length){results.innerHTML='<div class="site-search-empty">No matching posts.</div>';return;}
        results.innerHTML=matches.map(d=>{
          const date=d.date?new Date(d.date).toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric'}):'';
          return '<a class="site-search-result" href="'+escHtml(d.url)+'">'+
            '<span class="site-search-result-title">'+escHtml(d.title)+'</span>'+
            (date?'<span class="site-search-result-meta">'+escHtml(date)+'</span>':'')+
            (d.excerpt?'<span class="site-search-result-excerpt">'+escHtml(d.excerpt)+'</span>':'')+
          '</a>';
        }).join('');
      }catch(err){
        results.innerHTML='<div class="site-search-empty">Search is temporarily unavailable.</div>';
      }
    };
    const open=()=>{
      panel.classList.add('is-open');
      button.setAttribute('aria-expanded','true');
      setTimeout(()=>input.focus(),0);
    };
    const hide=()=>{
      panel.classList.remove('is-open');
      button.setAttribute('aria-expanded','false');
    };

    button.setAttribute('aria-expanded','false');
    button.addEventListener('click',e=>{e.preventDefault();panel.classList.contains('is-open')?hide():open();});
    close.addEventListener('click',hide);
    input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(draw,140);});
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&panel.classList.contains('is-open'))hide();});
    document.addEventListener('click',e=>{
      if(panel.classList.contains('is-open')&&!panel.contains(e.target)&&!button.contains(e.target))hide();
    });
  }
  window.addEventListener('load',initSiteSearch);
})();
