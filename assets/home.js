(() => {
  'use strict';
  const $ = id => document.getElementById(id);
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
      const html = [...containers,...other].map(game => {
        const href = `catalogue.html?game=${encodeURIComponent(game.id)}`;
        const cover = COVER[game.id];
        const title = game.ungrouped ? 'Others' : game.title;
        return `<a role="listitem" class="game-tile ${cover?'has-cover':'art-abstract'}" href="${href}" aria-label="Browse ${escapeHTML(title)} — ${game.count} JAR records">
          <div class="tile-art" ${cover?`style="background-image:url('assets/covers/${cover}')"`:''}></div>
          <div class="tile-shapes" aria-hidden="true"><span>✦</span></div>
          <div class="tile-inner"><h3>${escapeHTML(title)}</h3></div></a>`;
      }).join('');
      $('game-grid').innerHTML=html;
    } catch (error) {
      $('game-grid').innerHTML = `<p class="load-error">Could not load the catalogue: ${escapeHTML(error.message)}. Start <code>python3 server.py</code> and reload.</p>`;
    }
  }
  init();
})();
