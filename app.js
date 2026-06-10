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
}

async function init() {
  try {
    const res = await fetch('data.json', { cache: 'no-store' });
    const data = await res.json();
    cpus = [...data.cpus].sort(sortByScoreDesc);
    gpus = [...data.gpus].sort(sortByScoreDesc);
    renderTrack(cpuTrack, cpus, 'cpu');
    renderTrack(gpuTrack, gpus, 'gpu');
  } catch (err) {
    console.error('Не удалось загрузить data.json:', err);
    cpuTrack.innerHTML = '<li class="item">Не удалось загрузить данные</li>';
    gpuTrack.innerHTML = '<li class="item">Не удалось загрузить данные</li>';
  }
}

init();
