const board = document.getElementById('board');
const cpuTrack = document.getElementById('cpu-track');
const gpuTrack = document.getElementById('gpu-track');

let cpus = [];
let gpus = [];

function getScore(item) {
  return item.stScore !== undefined ? item.stScore : item.score;
}

function sortByScoreDesc(a, b) {
  return getScore(b) - getScore(a);
}

function inRange(value, range) {
  if (!range || range.length !== 2) return false;
  const [min, max] = range;
  return value >= min && value <= max;
}

function renderTrack(container, items, side) {
  container.innerHTML = '';
  const maxScore = items.reduce((m, it) => Math.max(m, getScore(it)), 0);
  items.forEach((item, index) => {
    const li = document.createElement('li');
    li.className = 'item';
    li.dataset.id = item.id;
    li.dataset.score = getScore(item);
    li.dataset.side = side;
    const power = maxScore > 0 ? (getScore(item) / maxScore) * 100 : 0;
    li.dataset.power = power.toFixed(1);

    const row = document.createElement('div');
    row.className = 'item-row';

    const rank = document.createElement('span');
    rank.className = 'rank';
    rank.textContent = index + 1;

    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = item.name;

    if (item.verified) {
      const check = document.createElement('span');
      check.className = 'verified';
      check.textContent = '\u2713';
      check.title = 'Данные проверены человеком';
      check.setAttribute('aria-label', 'Проверено');
      name.appendChild(check);
    }

    const score = document.createElement('span');
    score.className = 'score';
    score.textContent = getScore(item).toLocaleString('ru-RU');

    row.append(rank, name, score);

    const bar = document.createElement('span');
    bar.className = 'bar';
    bar.style.setProperty('--power', power.toFixed(1));

    li.append(row, bar);
    li.addEventListener('click', () => handleSelect(item.id, side));
    container.appendChild(li);
  });
}

function clearMatches() {
  document.querySelectorAll('.item.match').forEach(el => el.classList.remove('match'));
  document.querySelectorAll('.item.active').forEach(el => el.classList.remove('active'));
  clearConnections();
}

function createConnectionsLayer() {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'connections');
  svg.setAttribute('aria-hidden', 'true');
  board.appendChild(svg);
  return svg;
}

let connectionsSvg = null;
let connectionsRaf = 0;

function clearConnections() {
  if (connectionsSvg) connectionsSvg.innerHTML = '';
  cancelAnimationFrame(connectionsRaf);
}

function scheduleDrawConnections() {
  cancelAnimationFrame(connectionsRaf);
  connectionsRaf = requestAnimationFrame(drawConnections);
}

function drawConnections() {
  if (!connectionsSvg) return;
  connectionsSvg.innerHTML = '';

  const activeEl = document.querySelector('.item.active');
  if (!activeEl) return;

  const boardRect = board.getBoundingClientRect();
  connectionsSvg.setAttribute('viewBox', `0 0 ${boardRect.width} ${boardRect.height}`);
  connectionsSvg.setAttribute('width', boardRect.width);
  connectionsSvg.setAttribute('height', boardRect.height);

  const activeRect = activeEl.getBoundingClientRect();
  const activeSide = activeEl.dataset.side;
  const x1 = activeSide === 'cpu'
    ? activeRect.right - boardRect.left
    : activeRect.left - boardRect.left;
  const y1 = activeRect.top + activeRect.height / 2 - boardRect.top;

  const matches = document.querySelectorAll('.item.match');
  matches.forEach((endEl) => {
    const endRect = endEl.getBoundingClientRect();
    const x2 = endEl.dataset.side === 'gpu'
      ? endRect.left - boardRect.left
      : endRect.right - boardRect.left;
    const y2 = endRect.top + endRect.height / 2 - boardRect.top;

    const dx = Math.max(40, Math.abs(x2 - x1) / 2);
    const c1x = x1 + (activeSide === 'cpu' ? dx : -dx);
    const c2x = x2 + (endEl.dataset.side === 'gpu' ? -dx : dx);

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M ${x1} ${y1} C ${c1x} ${y1}, ${c2x} ${y2}, ${x2} ${y2}`);
    path.setAttribute('marker-end', 'url(#arrow-head)');
    connectionsSvg.appendChild(path);
  });

  if (!connectionsSvg.querySelector('#arrow-head')) {
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', 'arrow-head');
    marker.setAttribute('viewBox', '0 0 10 10');
    marker.setAttribute('refX', '8');
    marker.setAttribute('refY', '5');
    marker.setAttribute('markerWidth', '6');
    marker.setAttribute('markerHeight', '6');
    marker.setAttribute('orient', 'auto-start-reverse');
    const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    arrow.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
    arrow.setAttribute('fill', 'var(--match)');
    marker.appendChild(arrow);
    defs.appendChild(marker);
    connectionsSvg.appendChild(defs);
  }
}

function findMatchingGpus(cpu) {
  return gpus.filter(g => inRange(g.score, cpu.gpuRange));
}

function findMatchingCpus(gpu) {
  return cpus.filter(c => inRange(gpu.score, c.gpuRange));
}

function handleSelect(id, side) {
  clearMatches();

  const selectedEl = document.querySelector(
    `.item[data-side="${side}"][data-id="${id}"]`
  );
  if (!selectedEl) return;
  selectedEl.classList.add('active');

  const matches = side === 'cpu'
    ? findMatchingGpus(cpus.find(c => c.id === id))
    : findMatchingCpus(gpus.find(g => g.id === id));

  if (!matches) return;

  const targetSide = side === 'cpu' ? 'gpu' : 'cpu';
  matches.forEach(m => {
    const el = document.querySelector(`.item[data-side="${targetSide}"][data-id="${m.id}"]`);
    if (el) el.classList.add('match');
  });

  scheduleDrawConnections();
}

async function init() {
  try {
    const data = window.PC_DATA;
    if (!data || !data.cpus || !data.gpus) {
      throw new Error('window.PC_DATA is missing — run `make init` to generate data.js');
    }
    cpus = [...data.cpus].sort(sortByScoreDesc);
    gpus = [...data.gpus].sort(sortByScoreDesc);
    renderTrack(cpuTrack, cpus, 'cpu');
    renderTrack(gpuTrack, gpus, 'gpu');
    connectionsSvg = createConnectionsLayer();
    window.addEventListener('scroll', scheduleDrawConnections, { passive: true });
    window.addEventListener('resize', scheduleDrawConnections);
  } catch (err) {
    console.error('Не удалось загрузить данные:', err);
    cpuTrack.innerHTML = '<li class="item">Не удалось загрузить данные</li>';
    gpuTrack.innerHTML = '<li class="item">Не удалось загрузить данные</li>';
  }
}

init();
