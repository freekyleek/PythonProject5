(function(){
  const imgs=document.querySelectorAll('.banner-slider .banner-img');
  if(!imgs.length) return;
  let idx=0;
  imgs.forEach((img,i)=>img.style.opacity=i===0?'1':'0');
  setInterval(()=>{
    const curr=imgs[idx];
    const next=imgs[(idx+1)%imgs.length];
    curr.style.opacity='0';
    next.style.opacity='1';
    idx=(idx+1)%imgs.length;
  },5000);
})();