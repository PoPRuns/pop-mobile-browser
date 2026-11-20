/* PoP Mobile — framework-free static catalogue. No game JARs are bundled. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmtBytes = (n) => n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;
  const safeUrl = (u) => /^https:\/\/archive\.org\/download\//.test(u) ? u : null;

  // Presets visible in freej2me-web's Display Size settings. The emulator's
  // underlying configuration accepts pixel dimensions; only use a custom size
  // if none of these presets can contain a future catalogue record.
  const SCREEN_PRESETS = Object.freeze([
    [96,65], [96,96], [104,80], [128,128], [132,176], [128,160],
    [176,208], [176,220], [208,208], [240,320], [320,240],
    [240,400], [352,416], [360,640], [640,360], [480,800], [800,480]
  ]);
  function chooseEmulatorResolution(catalogued) {
    const match = /^(\d{1,4})x(\d{1,4})$/i.exec(String(catalogued || '').trim());
    if (!match) return null;
    const width = Number(match[1]), height = Number(match[2]);
    if (width < 32 || height < 32 || width > 1024 || height > 1024) return null;
    const fitting = SCREEN_PRESETS.filter(([w,h]) => w >= width && h >= height);
    fitting.sort((a,b) => a[0]*a[1]-b[0]*b[1] ||
      (a[0]-width)+(a[1]-height)-(b[0]-width)-(b[1]-height) || a[0]-b[0]);
    const selected = fitting[0] || [width,height];
    return { width: selected[0], height: selected[1],
      original: `${width}x${height}`, exact: width === selected[0] && height === selected[1],
      custom: !fitting.length };
  }
  function playerResolutionNotice(resolution, status = 'requested') {
    if (!resolution) return;
    const label = `${resolution.width}x${resolution.height}`;
    const relation = resolution.exact ? 'matches the catalogue' :
      resolution.custom ? `custom size for ${resolution.original}` : `smallest fitting preset for ${resolution.original}`;
    if (status === 'failed') {
      $('play-notice').textContent = `Could not apply ${label} automatically. The game may use its previously saved screen size. Press Esc for emulator settings. Check the browser console for details.`;
    } else {
      const action = status === 'applied' ? 'Emulator LCD configured' : 'Configuring emulator LCD';
      $('play-notice').textContent = `${action}: ${label} (${relation}). Keyboard controls are under Controls below the game.`;
    }
  }

  const jarLibrary = window.PoPJarLibrary;
  let playTicket = 0;
  const state = { data: null, buildMap: new Map(), groupMap: new Map(), currentGame: null, selectedGroup: null, selectedBuild: null, selectedPlay: null, readyPlaySha: null, emulatorReady: false, jarSource: 'local', localHashes: new Set(), staticSite: !!document.querySelector('meta[name="pop-mobile-static"]'), lastFocus: null };
  const NUMPAD_SETTING_KEY = 'pop-mobile-numpad-mode-v1';
  let numpadMode = 'phone';
  try { if (localStorage.getItem(NUMPAD_SETTING_KEY) === 'standard') numpadMode = 'standard'; }
  catch { /* private / disabled storage */ }
  function updateNumpadMode(mode) {
    if (mode !== 'phone' && mode !== 'standard') return;
    numpadMode = mode;
    $('numpad-standard').checked = mode === 'standard';
    $('numpad-description').textContent = mode === 'standard'
      ? 'Standard numpad: pressing 1 sends 1, pressing 7 sends 7, etc. The keyboard’s top number row is unchanged.'
      : 'Phone keypad (default): numpad 1/2/3 send 7/8/9, and numpad 7/8/9 send 1/2/3. The keyboard’s top number row is unchanged.';
    try { localStorage.setItem(NUMPAD_SETTING_KEY, mode); } catch { /* private mode */ }
    const frame = $('player-holder')?.querySelector('iframe');
    if (frame?.contentWindow) {
      frame.contentWindow.postMessage({type: 'pop-mobile:numpad', mode}, location.origin);
    }
  }


  function toast(message) {
    const el = $('toast'); el.textContent = message; el.hidden = false;
    clearTimeout(toast.timer); toast.timer = setTimeout(() => { el.hidden = true; }, 2800);
  }
  function fillSelect(id, values) {
    const el = $(id);
    values.forEach((value) => {
      const option = document.createElement('option');
      option.value = value; option.textContent = value;
      el.append(option);
    });
  }
  function initialize(data) {
    state.data = data;
    state.currentGame = data.game;
    const currentGameTitle = data.game.ungrouped ? 'Others' : data.game.title;
    document.title = `PoP Mobile · ${currentGameTitle}`;
    $('game-title').textContent = currentGameTitle;
    $('result-dataset').textContent = data.game.sheet.toUpperCase();
    if (data.relatedFiles.length) {
      $('related-files-container').hidden = false;
      $('related-files-count').textContent = `(${data.relatedFiles.length})`;
      $('related-files-list').innerHTML = data.relatedFiles.map(f =>
        `<div class="related-file-entry"><strong>${escape(f.filename)}</strong>${f.notes?`<p>${escape(f.notes)}</p>`:''}</div>`).join('');
    }
    state.buildMap = new Map(data.builds.map(b => [b.id, b]));
    state.groupMap = new Map(data.groups.map(g => [g.id, g]));
    fillSelect('filter-resolution', [...new Set(data.builds.map(b => b.resolution).filter(Boolean))].sort((a,b) => {
      const [aw, ah] = a.split('x').map(Number), [bw, bh] = b.split('x').map(Number);
      return (aw*ah)-(bw*bh);
    }));
    fillSelect('filter-language', [...new Set(data.builds.map(b => b.language).filter(Boolean))].sort());
    for (const id of ['filter-search', 'filter-resolution', 'filter-language']) {
      $(id).addEventListener(id === 'filter-search' ? 'input' : 'change', render);
    }
    $('clear-filters').addEventListener('click', resetFilters);
    $('empty-clear').addEventListener('click', resetFilters);
    $('results').addEventListener('click', handleResultAction);
    $('details-body').addEventListener('click', handleDetailAction);
    $('close-info').addEventListener('click', () => closeModal('info-modal'));
    $('close-info-secondary').addEventListener('click', () => closeModal('info-modal'));
    $('close-details').addEventListener('click', () => closeModal('details-modal'));
    $('close-play').addEventListener('click', () => closeModal('play-modal'));
    $('restart-play').addEventListener('click', restartPlayer);
    $('player-fullscreen').addEventListener('click', togglePlayerFullscreen);
    $('numpad-standard').addEventListener('change', event => {
      updateNumpadMode(event.target.checked ? 'standard' : 'phone');
    });
    updateNumpadMode(numpadMode);
    $('jar-upload').addEventListener('click', () => $('jar-file-picker').click());
    $('jar-file-picker').addEventListener('change', onJarFilePicked);
    $('jar-forget').addEventListener('click', async () => {
      const build = state.buildMap.get(state.selectedPlay);
      if (!build) return;
      try {
        await jarLibrary.forget(build);
        state.readyPlaySha = null;
        $('restart-play').disabled = true;
        setJarStatus('Removed the browser-cached JAR. The current game can continue, but select the JAR again before restarting.');
        $('jar-forget').hidden = true;
      } catch (error) { setJarStatus(`Could not clear cache: ${error.message}`, true); }
    });

    window.addEventListener('message', (event) => {
      const frame = $('player-holder').querySelector('iframe');
      if (event.origin !== location.origin || !frame || event.source !== frame.contentWindow) return;
      if (event.data?.type !== 'pop-mobile:resolution' || !state.selectedPlay) return;
      const build = state.buildMap.get(state.selectedPlay);
      const selected = build && chooseEmulatorResolution(build.resolution);
      if (selected && selected.width === event.data.width && selected.height === event.data.height) {
        playerResolutionNotice(selected, event.data.ok ? 'applied' : 'failed');
      }
    });

    document.addEventListener('fullscreenchange', syncFullscreenButton);
    for (const modal of ['details-modal', 'info-modal', 'play-modal']) {
      $(modal).addEventListener('mousedown', event => { if (event.target === $(modal)) closeModal(modal); });
    }
    document.addEventListener('keydown', (e) => {
      // Esc first exits browser fullscreen; it must not also close the player.
      if (e.key === 'Escape' && document.fullscreenElement === $('player-stage')) return;
      if (e.key === 'Escape' && !['details-modal','play-modal','info-modal'].every(id => $(id).hidden)) {
        const open = ['play-modal','details-modal','info-modal'].find(id => !$(id).hidden);
        closeModal(open);
      }
    });
    window.addEventListener('hashchange', followDeepLink);
    render(); followDeepLink();
    const deepSha = new URLSearchParams(location.search).get('sha256');
    if (deepSha && state.buildMap.has(deepSha.toLowerCase())) {
      const build = state.buildMap.get(deepSha.toLowerCase());
      openGroup(build.group, build.id);
    }
  }
  function resetFilters() {
    $('filter-search').value = '';
    $('filter-resolution').value = '';
    $('filter-language').value = '';
    render();
  }
  function matchesBuild(b) {
    const q = $('filter-search').value.trim().toLocaleLowerCase();
    if ($('filter-resolution').value && b.resolution !== $('filter-resolution').value) return false;
    if ($('filter-language').value && b.language !== $('filter-language').value) return false;
    if (!q) return true;
    const g = state.groupMap.get(b.group);
    const searchText = [b.group, b.name, b.displayTitle, b.vendor, b.version, b.language, b.resolution, b.device, b.oldFilename, b.sourceFilenames, b.sha256, b.sha1, b.crc32, b.notesGeneral, b.notesGameplay, b.notesGameplay2, ...(g?.notes || [])].join(' ').toLocaleLowerCase();
    return q.split(/\s+/).every(term => searchText.includes(term));
  }
  function render() {
    if (!state.data) return;
    const filteredBuilds = state.data.builds.filter(matchesBuild);
    // Preserve the previous default group-number order without a sort control.
    filteredBuilds.sort((a,b) => a.group.localeCompare(b.group));
    $('result-count').textContent = `SHOWING ${filteredBuilds.length} JAR BUILDS`;
    $('results').className = 'jar-list';
    $('results').innerHTML = filteredBuilds.map(renderJarRow).join('');
    $('empty-state').hidden = filteredBuilds.length !== 0;
  }
  function isAvailable(b) {
    // A visitor can supply any catalogue build through the verified JAR picker.
    return true;
  }
  function renderJarRow(b) {
    const available = isAvailable(b);
    return `<article class="jar-row"><div class="jar-core"><div class="jar-eyebrow">${b.unclassified?'NEEDS REVIEW':escape(b.group)} <span aria-hidden="true">/</span> ${escape(b.resolution||'Screen unknown')} <span aria-hidden="true">/</span> ${escape(b.language || 'Unknown language')}</div><h3 class="jar-title">${escape(b.name || 'Untitled MIDlet')}</h3><div class="jar-sub">${escape(b.vendor||'Unknown vendor')} · v${escape(b.version||'?')} · ${fmtBytes(b.size)}</div><div class="jar-sha"><span>SHA-256</span> <code>${escape(b.sha256)}</code></div></div><div class="jar-actions"><button type="button" data-action="details" data-group="${escape(b.group)}" data-build="${escape(b.id)}">Details</button><button type="button" data-action="play" data-build="${escape(b.id)}" class="jar-go" ${available?'':'disabled title="No matching local JAR"'}>Play</button></div></article>`;
  }
  function handleResultAction(e) {
    const button = e.target.closest('button[data-action]'); if (!button) return;
    const { action, group, build } = button.dataset;
    if (action === 'details') openGroup(group, build);
    else if (action === 'play') play(build);
  }
  function showModal(id) {
    state.lastFocus = document.activeElement;
    $(id).hidden = false; document.body.classList.add('modal-open');
    $(id).querySelector('[role="dialog"]').focus();
  }
  function closeModal(id) {
    $(id).hidden = true;
    if (id === 'play-modal') {
      ++playTicket; // Ignore delayed file validation after closing the dialog.
      state.readyPlaySha = null;
      $('restart-play').disabled = true;
      if (document.fullscreenElement === $('player-stage')) {
        document.exitFullscreen().catch(() => {});
      }
      $('player-holder').replaceChildren();
    }
    if (id === 'details-modal' && location.hash.startsWith('#group/')) history.replaceState(null,'',location.pathname+location.search+'#catalogue');
    if (['details-modal','info-modal','play-modal'].every(id => $(id).hidden)) document.body.classList.remove('modal-open');
    if (state.lastFocus && typeof state.lastFocus.focus === 'function') state.lastFocus.focus();
  }
  function followDeepLink() {
    const match = /^#group\/([A-Za-z0-9_+.-]+)$/.exec(location.hash);
    if (match && state.groupMap.has(match[1])) openGroup(match[1], null, true);
  }
  function openGroup(id, buildId = null, fromHash = false) {
    const group = state.groupMap.get(id);
    if (!group) return;
    state.selectedGroup = group;
    state.selectedBuild = (buildId && state.buildMap.has(buildId)) ? buildId : group.buildIds[0];
    $('details-heading').textContent = group.unclassified ? `Needs review · entry ${group.id}` : `${group.collection} · ${group.id}`;
    renderGroupDetails();
    if ($('details-modal').hidden) showModal('details-modal');
    if (!fromHash && location.hash !== `#group/${id}`) history.replaceState(null,'',location.pathname+location.search+`#group/${id}`);
  }
  function renderGroupDetails() {
    const g = state.selectedGroup, b = state.buildMap.get(state.selectedBuild);
    if (!g || !b) return;
    const chips = g.buildIds.map((id,index) => {
      const v = state.buildMap.get(id), selected = v.id === b.id;
      return `<button type="button" class="build-chip ${selected ? 'selected':''}" aria-pressed="${selected}" data-action="select-build" data-build="${escape(v.id)}"><strong>#${index+1} · ${escape(v.resolution)}</strong><small>${escape(v.language||'?')} · ${escape(v.version||'?')}</small></button>`;
    }).join('');
    const notes = [b.notesGeneral, b.notesGameplay, b.notesGameplay2].filter(Boolean);
    const available = isAvailable(b);
    const links = b.urls.filter(safeUrl).map((url,index) => {
      const collection = url.includes('JARchiveLite_v11') ? 'Lite archive' : url.includes('JARchive_v11') ? 'Full archive' : 'Archive source';
      return `<a href="${escape(url)}" target="_blank" rel="noopener noreferrer" title="Third-party archive; availability not guaranteed">Source ${index+1} · ${collection} ↗</a>`;
    }).join('');
    $('details-body').innerHTML = `
      <div class="details-intro"><span class="pill accent">${g.count} unique SHA-256 builds</span><span class="pill">${escape(g.resolutions.join(' · '))}</span><p>Gameplay classification from the supplied catalogue. Not a claim of identical binaries.</p></div>
      ${g.notes.length?`<div class="details-note">${escape(g.notes[0])}</div>`:''}
      <div class="details-sublabel">SELECT A RECORDED JAR BUILD</div><div class="build-selector">${chips}</div>
      <div class="selected-build"><h3 class="build-title">${escape(b.name)}</h3><div class="build-subtitle">${escape(b.group)} · ${escape(b.version)} · ${escape(b.vendor||'Unknown vendor')}</div>
        <div class="meta-grid">${[
          ['Display',b.resolution||'Not recorded'],['Language',b.language],['Device',b.device||'Not recorded'],
          ['CLDC / MIDP',`${b.cldc||'?'} / ${b.midp||'?'}`],['Applet version',b.version],['In-game version',b.aboutVersion||'Not recorded'],
          ['In-game author',b.aboutAuthor||'Not recorded'],['File size',fmtBytes(b.size)],['Archive references',b.urls.length]
        ].map(([k,v])=>`<div class="meta-field"><span>${escape(k.toUpperCase())}</span><strong>${escape(v)}</strong></div>`).join('')}</div>
        <div class="build-actions"><button class="btn btn-primary" type="button" data-action="play" data-build="${escape(b.id)}" ${available?'':'disabled title="No matching local JAR found"'}>Play</button><button class="btn btn-outline" type="button" data-action="copy" data-copy="${escape(b.sha256)}">Copy SHA-256</button>${links ? `<a class="btn btn-outline" href="${escape(b.urls.find(safeUrl))}" rel="noopener noreferrer" target="_blank">Archive download ↗</a>` : ''}</div>
        <p class="emulator-help">${!state.emulatorReady?'Browser emulator runtime is unavailable. Check the deployment or local setup.':state.localHashes.has(b.sha256)?'A locally verified JAR is available. You can also choose a matching file to save it in browser storage.':'The player will check its verified browser cache. Otherwise, use the J2ME index and choose a matching JAR file.'}</p>
        ${links?`<div class="details-sublabel">EXTERNAL ARCHIVE SOURCES</div><div class="download-links">${links}</div>`:''}
        ${notes.length?`<div class="details-sublabel">RESEARCH NOTES</div><div class="notes-list">${notes.map(n=>`<p>${escape(n)}</p>`).join('')}</div>`:''}
        <div class="hash-fields">${[['CRC32',b.crc32],['SHA-1',b.sha1],['SHA-256',b.sha256]].map(([k,v])=>`<div><div><label>${k}</label><code>${escape(v)}</code></div><button type="button" data-action="copy" data-copy="${escape(v)}">Copy</button></div>`).join('')}</div>
        ${b.sourceFilenames?`<div class="details-sublabel">SOURCE FILENAME</div><div class="jar-sub">${escape(b.sourceFilenames)}</div>`:''}
        ${b.archivePaths?`<div class="details-sublabel">CATALOGUED ARCHIVE PATHS</div><div class="jar-sub">${escape(b.archivePaths)}</div>`:''}
      </div>`;
  }
  function handleDetailAction(e) {
    const button = e.target.closest('button[data-action]'); if (!button) return;
    if (button.dataset.action === 'select-build' && state.selectedGroup.buildIds.includes(button.dataset.build)) {
      state.selectedBuild = button.dataset.build; renderGroupDetails();
    } else if (button.dataset.action === 'copy') copyText(button.dataset.copy);
    else if (button.dataset.action === 'play') play(button.dataset.build);
  }
  async function copyText(text) {
    try { await navigator.clipboard.writeText(text); toast('Copied to clipboard'); }
    catch { toast('Clipboard blocked by browser settings'); }
  }
  async function checkEmulator() {
    let status = null;
    if (state.staticSite) {
      // Generated GitHub Pages builds have no Python API, and every user
      // brings their own verified game JAR. Test the actual deployed files.
      try {
        const files = ['emulator/run.html', 'emulator/freej2me-web.jar'];
        const checks = await Promise.all(files.map(async (file) => {
          const response = await fetch(new URL(file, document.baseURI), {method: 'HEAD'});
          return response.ok;
        }));
        state.emulatorReady = checks.every(Boolean);
      } catch (error) {
        state.emulatorReady = false;
        console.warn('PoP Mobile: static emulator files unavailable:', error);
      }
      state.localHashes.clear();
    } else {
      try {
        const response = await fetch('/api/status', {cache:'no-store'});
        if (response.ok) {
          status = await response.json();
          state.emulatorReady = !!status.emulatorReady;
          state.jarSource = status.jarSource || 'local';
          state.localHashes = new Set(status.localJarHashes || []);
        }
      } catch { /* A local server is needed for the optional local JAR directory. */ }
    }
    render();
    if (!$('details-modal').hidden) renderGroupDetails();
    $('play-notice').textContent = state.staticSite
      ? 'Playing SHA-256-verified JARs saved in your browser. No game files are hosted or downloaded automatically.'
      : 'Using SHA-256-verified local JARs or files saved in your browser. No automatic downloads; browser emulation is experimental.';
    $('source-instructions').textContent = state.staticSite
      ? 'Open the J2ME index for the exact SHA-256, download your own JAR, and choose it in the player. The browser verifies and caches the file; no local Python server is required.'
      : 'If a matching file is in the local JAR folder, the server verifies and serves it. Otherwise, open the J2ME index for the exact SHA-256, download the JAR, and choose it in the player. Your browser verifies and caches it.';
    const el = $('emulator-status');
    el.textContent = state.emulatorReady
      ? '✓ Browser emulator detected. Choose a matching JAR build and press Play.'
      : state.staticSite
        ? 'Emulator files not found in the Pages deployment. Check the build/deployment workflow.'
        : 'Emulator runtime not found. Verify vendor/freej2me-web/web/run.html and freej2me-web.jar, then restart the server.';
  }
  function showInfo() {
    if ($('info-modal').hidden) showModal('info-modal');
    checkEmulator();
  }
  function setJarStatus(message, error = false) {
    const el = $('jar-status');
    el.textContent = message;
    el.classList.toggle('jar-error', error);
  }
  function loadPlayerOnce(build, ticket, status, cachedCopy = false) {
    if (ticket !== playTicket || $('play-modal').hidden || state.selectedPlay !== build.sha256) return;
    state.readyPlaySha = build.sha256;
    $('restart-play').disabled = false;
    setJarStatus(status);
    $('jar-forget').hidden = !cachedCopy;
    restartPlayer();
  }
  async function loadVerifiedLocal(build, ticket) {
    setJarStatus('Checking that the local JAR is accessible to the emulator…');
    const check = await jarLibrary.reachableLocal(build);
    if (ticket !== playTicket || $('play-modal').hidden || state.selectedPlay !== build.sha256) return;
    if (check.ok) {
      loadPlayerOnce(build, ticket, 'Using the SHA-256-verified local JAR from the preview server.');
    } else {
      state.readyPlaySha = null;
      $('restart-play').disabled = true;
      setJarStatus('The local JAR is currently unavailable (' + check.reason + '). ' +
        'Choose the matching JAR file, or start the server with --jar-dir pointing to your JAR collection.', true);
    }
  }
  // Never fetch an external JAR automatically. A user-provided file is checked
  // by size, ZIP signature and SHA-256 before it reaches Cache Storage.
  async function prepareSource(build, ticket) {
    const current = () => ticket === playTicket && state.selectedPlay === build.sha256 && !$('play-modal').hidden;
    const localExists = state.localHashes.has(build.sha256);
    setJarStatus('Checking this browser’s verified JAR cache…');
    try {
      await jarLibrary.ensureWorker();
      if (!current()) return;
      if (await jarLibrary.cached(build)) {
        loadPlayerOnce(build, ticket, 'Using a verified JAR saved in this browser.', true);
        return;
      }
    } catch (error) {
      if (!current()) return;
      if (localExists) {
        await loadVerifiedLocal(build, ticket);
      } else {
        setJarStatus('Browser cache is unavailable: ' + error.message + '. Use HTTPS or localhost and enable site storage to import JARs.', true);
      }
      return;
    }
    if (!current()) return;
    if (localExists) {
      await loadVerifiedLocal(build, ticket);
    } else {
      setJarStatus('JAR not cached. Open its SHA-256 entry on the J2ME index, download the file, then click Choose JAR file…');
    }
  }

  async function onJarFilePicked(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    const build = state.buildMap.get(state.selectedPlay);
    if (!file || !build) return;
    const ticket = ++playTicket;
    setJarStatus('Checking selected file against the catalogue SHA-256…');
    try {
      await jarLibrary.storeFile(build, file);
      loadPlayerOnce(build, ticket, `File “${file.name}” matches SHA-256. Saved in this browser and ready to play.`, true);
    } catch (error) {
      if (ticket === playTicket) setJarStatus('Could not load “' + file.name + '”: ' + error.message, true);
    }
  }
  function play(sha) {
    if (!state.buildMap.has(sha)) return;
    const build = state.buildMap.get(sha);
    if (!state.emulatorReady) { showInfo(); return; }
    state.selectedPlay = sha;
    state.readyPlaySha = null;
    $('restart-play').disabled = true;
    const ticket = ++playTicket;
    const screen = chooseEmulatorResolution(build.resolution);
    $('play-heading').textContent = `${build.name} · ${build.resolution}${screen && !screen.exact ? ` → ${screen.width}x${screen.height}` : ''}`;
    if (!$('details-modal').hidden) $('details-modal').hidden = true;
    if ($('play-modal').hidden) showModal('play-modal');
    $('player-holder').replaceChildren();
    $('player-controls').open = false;
    $('jar-forget').hidden = true;
    $('jar-file-picker').value = '';
    $('jar-index-link').href = jarLibrary.archiveSearchLink(build);
    playerResolutionNotice(screen);
    prepareSource(build, ticket);
  }
  // The upstream emulator's "Maximize" key toggles fractional scaling, not
  // fullscreen. We fullscreen our own player stage with the browser API.
  function syncFullscreenButton() {
    const active = document.fullscreenElement === $('player-stage');
    const button = $('player-fullscreen');
    button.setAttribute('aria-pressed', String(active));
    button.setAttribute('aria-label', active ? 'Exit fullscreen' : 'Enter fullscreen');
    button.title = active ? 'Exit fullscreen' : 'Enter fullscreen';
    $('player-fullscreen-icon').textContent = active ? '⤢' : '⛶';
    $('player-fullscreen-label').textContent = active ? 'Exit fullscreen' : 'Fullscreen';
    // The button takes focus away from the game; give it back after resizing.
    if (!$('play-modal').hidden) requestAnimationFrame(focusPlayer);
  }
  function focusPlayer() {
    const frame = $('player-holder').querySelector('iframe');
    if (!frame) return;
    try {
      const canvas = frame.contentDocument?.getElementById('display');
      if (canvas && getComputedStyle(canvas).display !== 'none') {
        canvas.focus({preventScroll: true});
      } else {
        frame.focus({preventScroll: true});
      }
    } catch {
      frame.focus({preventScroll: true});
    }
  }
  async function togglePlayerFullscreen() {
    const stage = $('player-stage');
    try {
      if (document.fullscreenElement === stage) {
        await document.exitFullscreen();
      } else if (document.fullscreenElement) {
        toast('Exit the current fullscreen view before opening the player.');
      } else if (!stage.requestFullscreen || !document.fullscreenEnabled) {
        toast('Fullscreen is not supported here; try Firefox F11.');
      } else {
        await stage.requestFullscreen();
      }
    } catch (error) {
      console.warn('Could not toggle player fullscreen:', error);
      toast('Fullscreen was blocked by the browser; try Firefox F11.');
    }
  }
  function restartPlayer() {
    if (!state.selectedPlay || state.readyPlaySha !== state.selectedPlay) return;
    const frame = document.createElement('iframe');
    frame.title = 'Java ME browser player';
    frame.allow = 'autoplay; fullscreen';
    frame.setAttribute('allowfullscreen', '');
    // Avoid false error messages: the Python recovery/local backend can serve
    // verified JARs even when this iframe lacks a Service Worker controller.
    // Successful emulator gameplay is authoritative; do not overwrite its
    // status with a warning based on navigator.serviceWorker.controller.
    // No mobile=1: that opt-in makes freej2me-web draw its virtual keypads.
    const build = state.buildMap.get(state.selectedPlay);
    const screen = build && chooseEmulatorResolution(build.resolution);
    const params = new URLSearchParams({jar: state.selectedPlay + '.jar', fractionScale: '1', numpad: numpadMode});
    if (screen) {
      params.set('screenWidth', String(screen.width));
      params.set('screenHeight', String(screen.height));
      playerResolutionNotice(screen);
    }
    frame.src = new URL(`emulator/run.html?${params.toString()}`, document.baseURI).href;
    $('player-holder').replaceChildren(frame);
  }
  async function load() {
    try {
      const response = await fetch('data/catalogue.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const entire = await response.json();
      if (!Array.isArray(entire.groups) || !Array.isArray(entire.builds) || !Array.isArray(entire.games)) throw new Error('Invalid full-catalogue format');
      const requested = new URLSearchParams(location.search).get('game') || 'harem-adventures';
      const game = entire.games.find(g => g.id === requested);
      if (!game) throw new Error('Unknown collection: ' + requested + '. Choose a game from the home page.');
      const builds = entire.builds.filter(b => b.game === game.id);
      const groups = entire.groups.filter(g => g.game === game.id);
      const data = {game, allGames: entire.games, builds, groups,
        relatedFiles: (entire.relatedFiles || []).filter(f => f.game === game.id),
        stats: {builds:builds.length, groups:game.groups,
          resolutions:new Set(builds.map(b => b.resolution).filter(Boolean)).size,
          languages:new Set(builds.map(b => b.language).filter(Boolean)).size}};
      initialize(data);
      jarLibrary.ensureWorker().catch(error => console.warn('Browser JAR cache not ready:', error));
      checkEmulator();
    } catch (error) {
      $('result-count').textContent='COULD NOT LOAD CATALOGUE';
      $('results').innerHTML=`<p style="color:#dfb587">${escape(error.message)}. Start the local server with <code>python3 server.py</code> rather than opening index.html directly.</p>`;
    }
  }
  load();
})();
