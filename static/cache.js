// Simple IndexedDB cache for universe stats with 1-hour TTL
(function () {
  const DB_NAME = 'universe-stats';
  const STORE = 'universes';
  const DB_VERSION = 1;
  const ONE_HOUR_MS = 60 * 60 * 1000;

  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = function (e) {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE, { keyPath: 'key' });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  function idbGet(db, key) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const store = tx.objectStore(STORE);
      const req = store.get(key);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  }

  function idbSet(db, record) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      const store = tx.objectStore(STORE);
      const req = store.put(record);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async function fetchUniverseWithCache(region, universe, ttlMs = ONE_HOUR_MS) {
    const key = region + '|' + universe;
    try {
      const db = await openDb();
      const cached = await idbGet(db, key);
      const now = Date.now();
      if (cached && cached.timestamp && now - cached.timestamp < ttlMs && Array.isArray(cached.data)) {
        return cached.data;
      }
      const url = `/api/universe?region=${encodeURIComponent(region)}&universe=${encodeURIComponent(universe)}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      await idbSet(db, { key, timestamp: now, data });
      return data;
    } catch (e) {
      // Fallback to network on DB errors
      const url = `/api/universe?region=${encodeURIComponent(region)}&universe=${encodeURIComponent(universe)}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      return await resp.json();
    }
  }

  function formatNum(n) {
    if (n === null || n === undefined) return '-';
    const val = Number(n);
    if (Number.isNaN(val)) return '-';
    return val.toFixed(2);
  }

  function renderRows(tbody, rows) {
    tbody.innerHTML = '';
    rows.forEach((r) => {
      const price = r.price;
      const sma200 = r.sma200;
      const tr = document.createElement('tr');
      const isAbove = price != null && sma200 != null && price >= sma200;
      tr.className = isAbove ? 'above200' : 'below200';
      tr.innerHTML = [
        `<td class="ticker">${r.symbol}</td>`,
        `<td class="num">${formatNum(r.price)}</td>`,
        `<td class="num">${formatNum(r.sma50)}</td>`,
        `<td class="num">${formatNum(r.sma200)}</td>`,
        `<td class="num strong">${r.pct_above_200dma != null ? formatNum(r.pct_above_200dma) + '%' : '-'}</td>`,
        `<td class="num">${formatNum(r.low_52w)}</td>`,
        `<td class="num">${formatNum(r.high_52w)}</td>`,
        `<td class="num">${r.pct_from_52w_low != null ? formatNum(r.pct_from_52w_low) + '%' : '-'}</td>`,
        `<td class="num">${r.pct_from_52w_high != null ? formatNum(r.pct_from_52w_high) + '%' : '-'}</td>`,
      ].join('');
      tbody.appendChild(tr);
    });
  }

  async function initUniverseSections() {
    const sections = document.querySelectorAll('.universe-section');
    for (const wrapper of sections) {
      const region = wrapper.getAttribute('data-region');
      const universe = wrapper.getAttribute('data-universe');
      const table = wrapper.querySelector('table.sortable-table');
      const tbody = table ? table.tBodies[0] : null;
      if (!region || !universe || !tbody) continue;
      // Leave loading row until data arrives
      try {
        const data = await fetchUniverseWithCache(region, universe);
        renderRows(tbody, data);
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="9">Failed to load data</td></tr>`;
      }
    }
  }

  document.addEventListener('DOMContentLoaded', initUniverseSections);
})();


