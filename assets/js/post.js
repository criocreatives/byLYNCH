/* Post-only rendering. Preparation preserves media nodes and authored copy;
   ordered masonry handles sizing separately. */
export function prepareGallery(grid){
  if(!grid || grid.dataset.galleryPrepared)return;
  normalizePostTextNodes(grid);
  normalizeNestedPostGalleries(grid);
  normalizeStandalonePostImages(grid);
  markFullWidthEmbeds(grid);
  grid.dataset.galleryPrepared='true';
}
  function cleanImageLists(){
    document.querySelectorAll('.entry-content li').forEach(li=>{if(li.querySelector('img')){li.style.listStyle='none';li.style.marginLeft='0';li.style.paddingLeft='0';const p=li.parentElement;if(p){p.classList.add('image-list');}}});
  }
  function normalizePostTextNodes(grid){

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
          return;
        }
        startParagraph(node).appendChild(node);
        return;
      }

      if(node.nodeType!==Node.ELEMENT_NODE)return;

      if(node.tagName==='HR'){
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
      if(!plain || /^[,;:.!?'"“”‘’\-–—…]+(?:\s+(?:and|or))?$/i.test(plain))p.classList.add('legacy-spacer');
    });
  }
  function normalizeNestedPostGalleries(grid){
    [...grid.children].forEach(child=>{
      const imgs=[...child.querySelectorAll('img')];
      if(!imgs.length && !child.textContent.trim() &&
         child.matches('.wp-gallery,.wp-block-gallery,.wp-block-image,h1,h2,h3,h4,h5,h6,p')){
        child.classList.add('legacy-spacer');
        return;
      }
      if(imgs.length<2)return;
      const galleryLike=child.matches('.wp-block-gallery,.wp-block-coblocks-gallery-stacked,.gallery,.wp-gallery,[class*="gallery"]') ||
        !!child.querySelector('.wp-block-gallery,.coblocks-gallery,.gallery,.wp-gallery,[class*="gallery"]');
      if(!galleryLike && child.textContent.trim())return;
      const figures=imgs.map(img=>img.closest('figure'));
      // Flatten only complete single-photo figures with no surrounding copy or
      // other media. Ambiguous legacy containers stay intact as a masonry item.
      const safe=figures.every(figure=>figure && figure!==child && child.contains(figure) && figure.querySelectorAll('img').length===1) &&
        new Set(figures).size===imgs.length && !child.querySelector('iframe,video,audio') &&
        child.textContent.replace(/\s/g,'')===figures.map(f=>f.textContent).join('').replace(/\s/g,'');
      if(!safe)return;
      const fragment=document.createDocumentFragment();
      const figureSet=new Set(figures);
      const move=node=>{
        if(figureSet.has(node)){
          node.classList.add('masonry-item');
          fragment.appendChild(node);
        }else if(node.nodeType===Node.TEXT_NODE || node.nodeType===Node.COMMENT_NODE){
          fragment.appendChild(node);
        }else [...node.childNodes].forEach(move);
      };
      [...child.childNodes].forEach(move);
      if(child.id && !figures[0].id)figures[0].id=child.id;
      child.replaceWith(fragment);
    });
  }
  function normalizeStandalonePostImages(grid){
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
        while(child.firstChild)figure.appendChild(child.firstChild);
      }
    });
  }
  function markFullWidthEmbeds(grid){
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

    grid.style.height=Math.max(0,Math.max(0,...heights)-gap)+'px';
  }
  function initBkMasonry(){
    const grid=document.querySelector('.bk-redesign .entry-content');
    if(!grid)return;
    prepareGallery(grid);
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

window.addEventListener('load',()=>{cleanImageLists();initBkMasonry();});
let resizeTimer;
window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(layoutBkMasonry,180);});
