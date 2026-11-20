(() => {
  'use strict';
  const escapeHTML = s => String(s ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const COVER = {
    'sands-of-time':'sands-of-time.jpg','warrior-within':'warrior-within.jpg',
    'two-thrones':'two-thrones.jpg','prince-2008':'prince-2008.jpg',
    'forgotten-sands':'forgotten-sands.jpg','classic':'classic.jpg',
    'classic-two-thrones':'two-thrones.jpg'
  };
  async function init() {
    try {
      const result = await fetch('data/catalogue.json');
      if (!result.ok) throw new Error(`HTTP ${result.status}`);
      const data = await result.json();
      const containers = data.games.filter(game=>!game.ungrouped);
      const other = data.games.filter(game=>game.ungrouped);
      const html = [...containers,...other].map((game, i) => {
        const href = `catalogue.html?game=${encodeURIComponent(game.id)}`;
        const cover = COVER[game.id];
        return `<a role="listitem" class="game-tile ${cover?'has-cover':'art-abstract'} ${game.ungrouped?'unreviewed':''}" href="${href}" aria-label="Browse ${escapeHTML(game.title)} — ${game.count} JAR records">
          <div class="tile-art" ${cover?`style="background-image:url('assets/covers/${cover}')"`:''}></div>
          <div class="tile-shapes" aria-hidden="true"><span>✦</span></div>
          <div class="tile-inner"><div class="tile-top"><span>${String(i+1).padStart(2,'0')} / ${game.ungrouped?'RESEARCH QUEUE':'MOBILE ARCHIVE'}</span><span class="tile-year">${escapeHTML(game.year)}</span></div>
          <div class="tile-bottom"><h3>${escapeHTML(game.title)}</h3><p>${escapeHTML(game.description)}</p><div class="tile-meta"><span>${game.count} JARs</span><span>${game.ungrouped?'UNCLASSIFIED':`${game.groups} GROUPS`}</span><span class="arrow" aria-hidden="true">↗</span></div></div></div></a>`;
      }).join('');
      $('game-grid').innerHTML=html;
    } catch (error) {
      $('game-grid').innerHTML = `<p class="load-error">Could not load the catalogue: ${escapeHTML(error.message)}. Start <code>python3 server.py</code> and reload.</p>`;
    }
  }
  init();
})();
