document.addEventListener('DOMContentLoaded', function () {
  function parseNumeric(text) {
    if (text == null) return NaN;
    const cleaned = String(text).replace(/[^0-9\.\-]/g, '').trim();
    if (!cleaned) return NaN;
    const val = parseFloat(cleaned);
    return isNaN(val) ? NaN : val;
  }

  function compareValues(aText, bText) {
    const aNum = parseNumeric(aText);
    const bNum = parseNumeric(bText);
    const aIsNum = !isNaN(aNum);
    const bIsNum = !isNaN(bNum);
    if (aIsNum && bIsNum) {
      if (aNum < bNum) return -1;
      if (aNum > bNum) return 1;
      return 0;
    }
    // Fallback to string compare (case-insensitive)
    const aStr = String(aText || '').toLowerCase();
    const bStr = String(bText || '').toLowerCase();
    if (aStr < bStr) return -1;
    if (aStr > bStr) return 1;
    return 0;
  }

  function clearIndicators(thElems) {
    Array.prototype.forEach.call(thElems, function (th) {
      th.removeAttribute('aria-sort');
      const ind = th.querySelector('.sort-indicator');
      if (ind) ind.textContent = '';
      th.dataset.sortDir = '';
    });
  }

  function sortTableByColumn(table, colIndex, direction) {
    const tbody = table.tBodies[0];
    const rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
    rows.sort(function (rowA, rowB) {
      const aText = rowA.cells[colIndex] ? rowA.cells[colIndex].textContent.trim() : '';
      const bText = rowB.cells[colIndex] ? rowB.cells[colIndex].textContent.trim() : '';
      const cmp = compareValues(aText, bText);
      return direction === 'asc' ? cmp : -cmp;
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
  }

  function initTable(table) {
    const thead = table.tHead;
    if (!thead) return;
    const headers = thead.rows[0].cells;
    Array.prototype.forEach.call(headers, function (th, idx) {
      th.style.cursor = 'pointer';
      th.addEventListener('click', function () {
        const current = th.dataset.sortDir === 'asc' ? 'desc' : 'asc';
        clearIndicators(headers);
        th.dataset.sortDir = current;
        th.setAttribute('aria-sort', current === 'asc' ? 'ascending' : 'descending');
        const ind = th.querySelector('.sort-indicator');
        if (ind) ind.textContent = current === 'asc' ? '▲' : '▼';
        sortTableByColumn(table, idx, current);
      });
    });
  }

  function initFilter(wrapper) {
    const input = wrapper.querySelector('.table-filter');
    const table = wrapper.querySelector('table.sortable-table');
    if (!input || !table) return;
    input.addEventListener('input', function () {
      const q = input.value.trim().toLowerCase();
      const rows = table.tBodies[0].rows;
      Array.prototype.forEach.call(rows, function (row) {
        const tickerCell = row.querySelector('td.ticker');
        const text = (tickerCell ? tickerCell.textContent : '').toLowerCase();
        row.style.display = q && text.indexOf(q) === -1 ? 'none' : '';
      });
    });
  }

  const tables = document.querySelectorAll('table.sortable-table');
  Array.prototype.forEach.call(tables, initTable);
  const wrappers = document.querySelectorAll('.table-wrapper');
  Array.prototype.forEach.call(wrappers, initFilter);
});


