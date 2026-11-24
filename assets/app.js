/* PoP Mobile — framework-free static catalogue. No game JARs are bundled. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmtBytes = (n) => n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;

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

  function playerResolution(build) {
    try {
      const saved = JSON.parse(localStorage.getItem('pop-mobile-resolution-v1:' + build.sha256));
      if ([saved?.width, saved?.height].every(n => Number.isInteger(n) && n >= 32 && n <= 1024)) return saved;
    } catch { /* Missing, corrupt or disabled browser storage. */ }
    return chooseEmulatorResolution(build.resolution);
  }

  const jarLibrary = window.PoPJarLibrary;
  let playTicket = 0;
  let jarStatusTimer = null;
  const JAR_STATUS_DURATION_MS = 5000;
  const state = { data: null, buildMap: new Map(), groupMap: new Map(), currentGame: null, expandedBuilds: new Set(), activeFamily: null, selectedPlay: null, readyPlaySha: null, readyPlaySource: null, emulatorReady: false, jarSource: 'local', localHashes: new Set(), staticSite: !!document.querySelector('meta[name="pop-mobile-static"]'), lastFocus: null };
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
    state.activeFamily = null;
    const flagged = data.builds.some(b => b.unplayable);
    $('filter-unplayable-wrap').hidden = !flagged;
    $('filter-unplayable').checked = false;
    $('filter-unplayable').addEventListener('change', render);
    $('families').addEventListener('click', event => {
      const button = event.target.closest('[data-family]');
      if (!button) return;
      state.activeFamily = button.dataset.family;
      render();
    });
    $('family-back').addEventListener('click', () => {state.activeFamily = null; render();});
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
    $('close-info').addEventListener('click', () => closeModal('info-modal'));
    $('close-info-secondary').addEventListener('click', () => closeModal('info-modal'));
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
        state.readyPlaySource = null;
        $('restart-play').disabled = true;
        setJarStatus('Removed the browser-cached JAR. The current game can continue, but select the JAR again before restarting.');
        $('jar-forget').hidden = true;
      } catch (error) { setJarStatus(`Could not clear cache: ${error.message}`, true); }
    });

    window.addEventListener('message', (event) => {
      const frame = $('player-holder').querySelector('iframe');
      if (event.origin !== location.origin || !frame || event.source !== frame.contentWindow) return;
      if (!state.selectedPlay) return;
      if (event.data?.type === 'pop-mobile:jar-error') {
        setJarStatus('Could not load cached JAR: ' + event.data.error, true);
        return;
      }
      if (event.data?.type !== 'pop-mobile:resolution') return;
      if (!event.data.ok) console.warn('Emulator display resolution could not be applied; use Esc for emulator settings.');
      else if ([event.data.width, event.data.height].every(n => Number.isInteger(n) && n >= 32 && n <= 1024)) {
        const build = state.buildMap.get(state.selectedPlay);
        if (build) $('player-report-issue').href = playerIssueUrl(build, event.data);
      }
    });

    document.addEventListener('fullscreenchange', syncFullscreenButton);
    for (const modal of ['info-modal', 'play-modal']) {
      $(modal).addEventListener('mousedown', event => { if (event.target === $(modal)) closeModal(modal); });
    }
    document.addEventListener('keydown', (e) => {
      // Esc first exits browser fullscreen; it must not also close the player.
      if (e.key === 'Escape' && document.fullscreenElement === $('player-stage')) return;
      if (e.key === 'Escape' && !['play-modal','info-modal'].every(id => $(id).hidden)) {
        const open = ['play-modal','info-modal'].find(id => !$(id).hidden);
        closeModal(open);
      }
    });
    window.addEventListener('hashchange', followDeepLink);
    render(); followDeepLink();
  }
  function resetFilters() {
    $('filter-search').value = '';
    $('filter-resolution').value = '';
    $('filter-language').value = '';
    $('filter-unplayable').checked = false;
    render();
  }
  function matchesBuild(b) {
    if (b.unplayable && !$('filter-unplayable').checked) return false;
    const q = $('filter-search').value.trim().toLocaleLowerCase();
    if ($('filter-resolution').value && b.resolution !== $('filter-resolution').value) return false;
    if ($('filter-language').value && b.language !== $('filter-language').value) return false;
    if (!q) return true;
    const g = state.groupMap.get(b.group);
    const searchText = [b.group, b.name, b.displayTitle, b.vendor, b.version, b.language, b.resolution, b.device, b.oldFilename, b.sourceFilenames, b.sha256, b.sha1, b.crc32, b.notesGeneral, b.notesGameplay, b.notesGameplay2, ...(g?.notes || [])].join(' ').toLocaleLowerCase();
    return q.split(/\s+/).every(term => searchText.includes(term));
  }
  const FAMILY_LABELS = Object.freeze({
    'HA-G01': 'Gameplay version 1',
    'HA-G02': 'Gameplay version 2',
    'HA-G03': 'Gameplay version 3'
  });
  const FAMILY_IMAGES = Object.freeze({
    'HA-G01': 'assets/previews/harem-g01.png',
    'HA-G02': 'assets/previews/harem-g02.png',
    'HA-G03': 'assets/previews/harem-g03.png'
  });
  function renderFamilyCard(family, builds) {
    const hidden = state.data.builds.filter(b => b.family === family.id && b.unplayable).length;
    const all = state.data.builds.filter(b => b.family === family.id).length;
    const image = FAMILY_IMAGES[family.id] || family.image;
    return `<button class="family-card" type="button" data-family="${escape(family.id)}"
      aria-label="Browse ${escape(FAMILY_LABELS[family.id] || family.id)}">
      ${image ? `<img src="${escape(image)}" alt="First-level screenshot for ${escape(family.id)}" loading="lazy">` : `<div class="family-image-placeholder" aria-hidden="true">◇</div>`}
      <span class="family-card-content"><span class="family-card-code">${escape(family.id)}</span>
      <strong>${escape(FAMILY_LABELS[family.id] || family.id)}</strong>
      <span>${builds.length} visible JAR builds${hidden ? ` · ${hidden} marked unplayable` : ''}</span></span>
    </button>`;
  }
  function render() {
    if (!state.data) return;
    const filteredBuilds = state.data.builds.filter(matchesBuild);
    filteredBuilds.sort((a,b) => a.group.localeCompare(b.group));
    const families = state.data.families || [];
    const hasFamilies = state.currentGame.id === 'harem-adventures' && families.length > 0;
    const overviewMode = hasFamilies && !state.activeFamily;
    document.body.classList.toggle('family-overview-mode', overviewMode);
    $('families').hidden = !hasFamilies;
    $('family-selection').hidden = !hasFamilies || !state.activeFamily;
    if (overviewMode) {
      const visibleFamilies = families.filter(f => filteredBuilds.some(b => b.family === f.id));
      $('families').innerHTML = visibleFamilies.map(f =>
        renderFamilyCard(f, filteredBuilds.filter(b => b.family === f.id))).join('');
      $('results').replaceChildren();
      $('results').hidden = true;
      $('result-count').textContent = '';
      $('empty-state').hidden = visibleFamilies.length !== 0;
    } else {
      const shown = hasFamilies ? filteredBuilds.filter(b => b.family === state.activeFamily) : filteredBuilds;
      $('results').hidden = false;
      $('results').className = 'jar-list';
      $('results').innerHTML = shown.map(renderJarRow).join('');
      if (hasFamilies) {
        $('family-selection-title').textContent = FAMILY_LABELS[state.activeFamily] || state.activeFamily;
        $('families').hidden = true;
      }
      $('result-count').textContent = `SHOWING ${shown.length} JAR BUILDS`;
      $('empty-state').hidden = shown.length !== 0;
    }
  }
  function isAvailable(b) {
    // A visitor can supply any catalogue build through the verified JAR picker.
    return true;
  }
  function renderJarRow(b) {
    const available = isAvailable(b);
    const expanded = state.expandedBuilds.has(b.id);
    const detailsId = `build-details-${b.id}`;
    return `<article class="jar-row"><div class="jar-summary"><div class="jar-core"><div class="jar-eyebrow">${b.unclassified?'NEEDS REVIEW':escape(b.group)} <span aria-hidden="true">/</span> ${escape(b.resolution||'Screen unknown')} <span aria-hidden="true">/</span> ${escape(b.language || 'Unknown language')}</div><h3 class="jar-title">${escape(b.name || 'Untitled MIDlet')}${b.unplayable ? ' <span class="unplayable-badge">Unplayable</span>' : ''}</h3><div class="jar-sub">${b.fpsLimit ? `<span class="fps-badge">Limit ${Number(b.fpsLimit)} FPS</span> ` : ''}${escape(b.vendor||'Unknown vendor')} · v${escape(b.version||'?')} · ${fmtBytes(b.size)}</div><div class="jar-sha"><span>SHA-256</span><code tabindex="0" aria-label="SHA-256 checksum: ${escape(b.sha256)}">${escape(b.sha256)}</code></div></div><div class="jar-actions"><button type="button" data-action="details" data-build="${escape(b.id)}" aria-expanded="${expanded}" aria-controls="${escape(detailsId)}">${expanded ? 'Hide details' : 'Details'}</button><button type="button" data-action="play" data-build="${escape(b.id)}" class="jar-go" ${available?'':'disabled title="No matching local JAR"'}>Play</button></div></div><div class="inline-build-details" id="${escape(detailsId)}" ${expanded ? '' : 'hidden'}>${expanded ? renderBuildDetails(b) : ''}</div></article>`;
  }
  function handleResultAction(e) {
    const button = e.target.closest('button[data-action]'); if (!button) return;
    const { action, build } = button.dataset;
    if (action === 'details') setBuildDetails(build, !state.expandedBuilds.has(build));
    else if (action === 'play') play(build);
    else if (action === 'copy') copyText(button.dataset.copy);
  }
  function showModal(id) {
    state.lastFocus = document.activeElement;
    $(id).hidden = false; document.body.classList.add('modal-open');
    $(id).querySelector('[role="dialog"]').focus();
  }
  function closeModal(id) {
    $(id).hidden = true;
    if (id === 'play-modal') {
      setJarStatus(''); // Clear a pending notification and cancel its timer.
      ++playTicket; // Ignore delayed file validation after closing the dialog.
      state.readyPlaySha = null;
      state.readyPlaySource = null;
      $('restart-play').disabled = true;
      if (document.fullscreenElement === $('player-stage')) {
        document.exitFullscreen().catch(() => {});
      }
      $('player-holder').replaceChildren();
    }
    if (['info-modal','play-modal'].every(id => $(id).hidden)) document.body.classList.remove('modal-open');
    if (state.lastFocus && typeof state.lastFocus.focus === 'function') state.lastFocus.focus();
  }
  function followDeepLink() {
    // Issue-report links identify the precise JAR, not the first member of its group.
    const sha = new URLSearchParams(location.search).get('sha256')?.toLowerCase();
    const match = /^#group\/([A-Za-z0-9_+.-]+)$/.exec(location.hash);
    const id = state.buildMap.has(sha) ? sha : (match && state.groupMap.get(match[1])?.buildIds[0]);
    if (id) {
      const build = state.buildMap.get(id);
      if (build?.unplayable) $('filter-unplayable').checked = true;
      if (build?.family && state.data.families?.length) state.activeFamily = build.family;
      render();
      setBuildDetails(id, true, true);
    }
  }
  function setBuildDetails(id, expanded, scroll = false) {
    const build = state.buildMap.get(id);
    const panel = $(`build-details-${id}`);
    if (!build || !panel) return;
    const row = panel.closest('.jar-row');
    const button = row.querySelector('button[data-action="details"]');
    if (expanded) {
      state.expandedBuilds.add(id);
      if (panel.hidden) panel.innerHTML = renderBuildDetails(build);
    } else {
      state.expandedBuilds.delete(id);
      panel.replaceChildren();
    }
    panel.hidden = !expanded;
    button.setAttribute('aria-expanded', String(expanded));
    button.textContent = expanded ? 'Hide details' : 'Details';
    if (scroll) row.scrollIntoView({block: 'start'});
  }
  function renderBuildDetails(b) {
    const fields = [
      ['Display', b.resolution], ['Language', b.language], ['Device', b.device],
      ['CLDC / MIDP', `${b.cldc || '?'} / ${b.midp || '?'}`],
      ['Applet version', b.version], ['In-game version', b.aboutVersion],
      ['In-game author', b.aboutAuthor], ['File size', fmtBytes(b.size)]
    ];
    return `<div class="meta-grid">${fields.map(([k,v]) => `<div class="meta-field"><span>${escape(k.toUpperCase())}</span><strong>${escape(v || 'Not recorded')}</strong></div>`).join('')}</div>
      <div class="hash-fields">${[['CRC32',b.crc32],['SHA-1',b.sha1],['SHA-256',b.sha256]].map(([k,v]) => `<div class="hash-row"><span class="hash-label">${k}</span><code tabindex="0" aria-label="${k} checksum: ${escape(v || 'Not recorded')}">${escape(v || 'Not recorded')}</code>${v ? `<button type="button" data-action="copy" data-copy="${escape(v)}" aria-label="Copy ${k}">Copy</button>` : ''}</div>`).join('')}</div>`;
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
    clearTimeout(jarStatusTimer); // A later status replaces the previous timer.
    jarStatusTimer = null;
    const el = $('jar-status');
    el.textContent = message;
    el.hidden = !message;
    el.classList.toggle('jar-error', error);
    if (message) {
      jarStatusTimer = setTimeout(() => {
        el.hidden = true;
        jarStatusTimer = null;
      }, JAR_STATUS_DURATION_MS);
    }
  }
  function playerIssueUrl(build, screen = playerResolution(build)) {
    const game = state.currentGame?.ungrouped ? 'Others' : (state.currentGame?.title || build.collection || build.game);
    const catalogueUrl = new URL('https://popruns.github.io/pop-mobile-browser/catalogue.html');
    catalogueUrl.searchParams.set('game', build.game);
    catalogueUrl.searchParams.set('sha256', build.sha256);
    const body = [
      '### What went wrong?',
      'Describe the problem and the steps to reproduce it.',
      '',
      '### Expected behavior',
      'Describe what should happen.',
      '',
      '### JAR build details',
      `- Collection: ${game}`,
      `- Game / JAR title: ${build.name}`,
      `- Source filename: ${build.sourceFilenames || build.oldFilename || 'Not recorded'}`,
      `- Vendor: ${build.vendor || 'Not recorded'}`,
      `- Version: ${build.version || 'Not recorded'}`,
      `- File size: ${fmtBytes(build.size)}`,
      `- Language: ${build.language || 'Not recorded'}`,
      `- Catalogued screen: ${build.resolution || 'Not recorded'}`,
      `- Emulator screen: ${screen ? `${screen.width}x${screen.height}` : 'Default'}`,
      `- FPS limit: ${build.fpsLimit || 'None'}`,
      `- SHA-256: ${build.sha256}`,
      `- Catalogue: ${catalogueUrl.href}`,
    ].join('\n');
    const issueUrl = new URL('https://github.com/PoPRuns/pop-mobile-browser/issues/new');
    issueUrl.searchParams.set('title', `[Playback] ${game}: ${build.name}`);
    issueUrl.searchParams.set('body', body);
    return issueUrl.href;
  }
  function loadPlayerOnce(build, ticket, status, cachedCopy = false) {
    if (ticket !== playTicket || $('play-modal').hidden || state.selectedPlay !== build.sha256) return;
    state.readyPlaySha = build.sha256;
    state.readyPlaySource = cachedCopy ? 'cache' : 'local';
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
      state.readyPlaySource = null;
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
      setJarStatus(''); // Keep the JAR chooser visible without the redundant cache-miss instructions.
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
    state.readyPlaySource = null;
    $('restart-play').disabled = true;
    const ticket = ++playTicket;
    // Emulator-specific canvas sizes belong in the runtime, not the window title.
    $('play-heading').textContent = [build.name, build.resolution].filter(Boolean).join(' · ');
    $('player-report-issue').href = playerIssueUrl(build);
    if ($('play-modal').hidden) showModal('play-modal');
    $('player-holder').replaceChildren();
    $('player-controls').open = false;
    $('jar-forget').hidden = true;
    $('jar-file-picker').value = '';
    $('jar-index-link').href = jarLibrary.archiveSearchLink(build);
    setJarStatus(''); // Prevent stale messages from a previous JAR flashing briefly.
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
    const screen = build && playerResolution(build);
    const params = new URLSearchParams({jar: state.selectedPlay + '.jar', fractionScale: '1', numpad: numpadMode, v: 'family-fps-1', jarSource: state.readyPlaySource, jarSize: String(build.size)});
    if ([15, 30, 60].includes(Number(build.fpsLimit))) params.set('fpsLimit', String(build.fpsLimit));
    if (screen) {
      params.set('screenWidth', String(screen.width));
      params.set('screenHeight', String(screen.height));
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
      const requested = new URLSearchParams(location.search).get('game') ?? 'harem-adventures';
      const game = entire.games.find(g => g.id === requested);
      if (!game) {
        location.replace(new URL('index.html', location.href).href);
        return;
      }
      const builds = entire.builds.filter(b => b.game === game.id);
      const groups = entire.groups.filter(g => g.game === game.id);
      const data = {game, allGames: entire.games, builds, groups,
        families: (entire.families || []).filter(f => f.game === game.id),
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
