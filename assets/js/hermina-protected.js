/* Hermina: browser-side AES-GCM encrypted story and originals. Do not put plaintext content in public repository. */
(()=>{'use strict';
const form=document.querySelector('#hermina-password-form');if(!form)return;
const out=document.querySelector('#hermina-protected-content');
const status=document.querySelector('#hermina-password-status');
const shell=document.querySelector('#hermina-password-shell');
const input=document.querySelector('#hermina-password-input');
const enc=new TextEncoder(),dec=new TextDecoder();
const unhex=s=>new Uint8Array(s.match(/.{2}/g).map(x=>parseInt(x,16)));
async function decrypt(key,name,info){
 const response=await fetch(info.path,{cache:'force-cache'});if(!response.ok)throw new Error('Protected media unavailable');
 const bytes=new Uint8Array(await response.arrayBuffer());
 const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:bytes.slice(0,12),additionalData:enc.encode(name)},key,bytes.slice(12));
 return plain;
}
const loadedUrls=[];
form.addEventListener('submit',async e=>{
 e.preventDefault();const value=input.value;if(!value)return;
 status.textContent='Unlocking…';const button=form.querySelector('button');button.disabled=true;
 try{
  const response=await fetch('/assets/protected/hermina/manifest.json',{cache:'no-cache'});
  if(!response.ok)throw new Error('Protected gallery unavailable');
  const manifest=await response.json();const material=await crypto.subtle.importKey('raw',enc.encode(value),'PBKDF2',false,['deriveKey']);
  const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:unhex(manifest.salt),iterations:manifest.iterations,hash:'SHA-256'},material,{name:'AES-GCM',length:256},false,['decrypt']);
  const article=dec.decode(await decrypt(key,manifest.article,manifest.items[manifest.article]));
  const template=document.createElement('template');template.innerHTML=article;
  const photos=[...template.content.querySelectorAll('img[data-protected-image]')];
  const urls=new Map();
  for(const img of photos){const name=img.dataset.protectedImage;
   if(!manifest.items[name])throw new Error('Gallery photograph missing');
   if(!urls.has(name)){const bytes=await decrypt(key,name,manifest.items[name]);
    const url=URL.createObjectURL(new Blob([bytes],{type:'image/webp'}));urls.set(name,url);loadedUrls.push(url);}
   img.src=urls.get(name);img.removeAttribute('data-protected-image');
  }
  out.replaceChildren(template.content);shell.hidden=true;out.hidden=false;
  input.value='';
  const lb=document.createElement('script');lb.src='/assets/js/lightbox.js';document.body.appendChild(lb);
  // The shared lightbox registers a load handler; initialize it without re-running site scripts.
  lb.onload=()=>window.dispatchEvent(new Event('load'));
 }catch(error){
  loadedUrls.splice(0).forEach(URL.revokeObjectURL);
  status.textContent=error.name==='OperationError'?'Incorrect password.':'Unable to unlock this gallery.';
 }finally{button.disabled=false;}
});
})();