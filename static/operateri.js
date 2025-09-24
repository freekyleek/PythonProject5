
(function(){
  function ready(fn){
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn, {once:true});
    else fn();
  }
  ready(function(){
    try{
      const GRID = document.getElementById('grid');
      const Q = document.getElementById('q');
      if(!GRID){
        console.error('[operateri] #grid nije pronađen u DOM-u.');
        return;
      }
      const host = document.querySelector('[data-source]');
      const dataUrl = (host && host.getAttribute('data-source')) || '/static/operateri.JSON';
      const EXCLUDE = new Set(['admin','superadmin']);
      const STATUS_ORDER = ['direktor','voditelj','prodaja','podrska','podrška','tehnicar','tehničar','serviser','servis','vozač','ostalo'];

      function normRole(v){
        v = (v||'').toString().trim();
        const l = v.toLowerCase();
        if (l === 'tehničar' || l === 'tehnicar') return 'tehničar';
        if (l === 'podrska') return 'podrška';
        if (l === 'serviser') return 'serviser';
        return l;
      }
      function roleDisplay(v){
        const n = normRole(v);
        switch(n){
          case 'tehničar': return 'Tehničar';
          case 'podrška':  return 'Podrška';
          case 'prodaja':  return 'Prodaja';
          case 'voditelj': return 'Voditelj';
          case 'direktor': return 'Direktor';
          case 'serviser': return 'Serviser';
          case 'servis':   return 'Servis';
          case 'vozač':    return 'Vozač';
          default: return (v||'').toString();
        }
      }
      function byStatus(ops){
        const map = new Map();
        for (const o of ops){
          const r = normRole(o.role || o.status || '');
          if (!r || EXCLUDE.has(r)) continue;
          if (!map.has(r)) map.set(r, []);
          map.get(r).push(o);
        }
        for (const [r, arr] of map){
          arr.sort((a,b)=> (a.last_name||'').localeCompare(b.last_name||'', 'hr') || (a.first_name||'').localeCompare(b.first_name||'', 'hr') || (a.username||'').localeCompare(b.username||'', 'hr'));
        }
        const keys = Array.from(map.keys());
        keys.sort((a,b)=>{
          const ai = STATUS_ORDER.indexOf(a);
          const bi = STATUS_ORDER.indexOf(b);
          if (ai !== -1 && bi !== -1) return ai - bi;
          if (ai !== -1) return -1;
          if (bi !== -1) return 1;
          return a.localeCompare(b,'hr');
        });
        return keys.map(k=>[k, map.get(k)]);
      }
      function profUrl(u){ return '/profile/' + encodeURIComponent(u||''); }

      function render(ops, q=''){
        GRID.innerHTML = '';
        const term = (q||'').trim().toLowerCase();
        const grouped = byStatus(ops);
        for (const [status, arr] of grouped){
          const list = term ? arr.filter(o => {
            const s = ((o.first_name||'') + ' ' + (o.last_name||'') + ' ' + (o.username||'')).toLowerCase();
            return s.includes(term);
          }) : arr;
          if (!list.length) continue;
          const box = document.createElement('section');
          box.className = 'box';
          box.setAttribute('aria-label', 'Grupa statusa ' + roleDisplay(status));
          box.innerHTML = '<h3>'+roleDisplay(status)+'</h3>';
          list.forEach(o => {
            const el = document.createElement('div');
            el.className = 'op';
            const avatarTxt = (o.username||'?').slice(0,1).toUpperCase();
            const avatar = `<div class="avatar" aria-hidden="true">${avatarTxt}</div>`;
            el.innerHTML = `${avatar}
              <div class="who">
                <div class="name">${(o.first_name||'') + ' ' + (o.last_name||'')}</div>
                <div class="small">@${o.username||''}</div>
              </div>
              <a class="btn" href="${profUrl(o.username)}" aria-label="Otvori profil za ${(o.first_name||'') + ' ' + (o.last_name||'')}">Profil</a>`;
            box.appendChild(el);
          });
          GRID.appendChild(box);
        }
        if (!GRID.children.length){
          const p = document.createElement('p');
          p.textContent = 'Nema operatera za prikaz.';
          GRID.appendChild(p);
        }
      }

      async function load(){
        try{
          const res = await fetch(dataUrl, {cache:'no-store'});
          if(!res.ok){
            console.error('[operateri] HTTP greška', res.status, dataUrl);
            GRID.innerHTML = '<p style="color:#b91c1c">Greška '+res.status+' pri učitavanju operatera.</p>';
            return;
          }
          const data = await res.json();
          const ops = Array.isArray(data) ? data : (Array.isArray(data.operators) ? data.operators : []);
          if(!Array.isArray(ops)){
            GRID.innerHTML = '<p style="color:#b91c1c">Nevažeći format JSON-a. Očekujem listu ili { "operators": [...] }.</p>';
            return;
          }
          render(ops);
          if(Q){ Q.addEventListener('input', e=>render(ops, e.target.value)); }
        }catch(e){
          console.error('[operateri] Greška pri fetchu:', e);
          GRID.innerHTML = '<p style="color:#b91c1c">Greška pri učitavanju operatera.</p>';
        }
      }
      load();
    }catch(err){
      console.error('[operateri] Fatal error:', err);
    }
  });
})();
