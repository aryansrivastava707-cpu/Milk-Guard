const form = document.getElementById('reading-form');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const readings = {
    ph: document.getElementById('ph').value,
    tds: document.getElementById('tds').value,
    temperature: document.getElementById('temperature').value
  };
  const response = await fetch('/predict', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(readings)});
  const data = await response.json();
  if (!response.ok) { alert(data.error); return; }
  const result = document.getElementById('result');
  const status = document.getElementById('status');
  result.classList.remove('hidden');
  status.textContent = data.result === 'NORMAL' ? '✓ NORMAL' : '⚠ SUSPICIOUS';
  status.className = data.result === 'NORMAL' ? 'normal' : 'suspicious';
  document.getElementById('probability').textContent = `Suspicious-screening score: ${data.suspicious_probability}%`;
  loadHistory();
});

async function loadHistory() {
  const rows = await (await fetch('/history')).json();
  if (!rows.length) return;
  let html = '<table><tr><th>Time</th><th>pH</th><th>TDS</th><th>Temp.</th><th>Result</th></tr>';
  rows.forEach(row => html += `<tr><td>${row.time}</td><td>${row.ph}</td><td>${row.tds}</td><td>${row.temperature}°C</td><td>${row.result}</td></tr>`);
  document.getElementById('history').innerHTML = html + '</table>';
}

async function loadLatestSensorReading() {
  const response = await fetch('/latest');
  const row = await response.json();
  if (!row) return;
  // An ESP32 posts through /predict; use the saved latest result to update the page.
  document.getElementById('ph').value = row.ph;
  document.getElementById('tds').value = row.tds;
  document.getElementById('temperature').value = row.temperature;
  const result = document.getElementById('result');
  const status = document.getElementById('status');
  result.classList.remove('hidden');
  status.textContent = row.result === 'NORMAL' ? '✓ NORMAL' : '⚠ SUSPICIOUS';
  status.className = row.result === 'NORMAL' ? 'normal' : 'suspicious';
  document.getElementById('probability').textContent = `Latest test: ${row.time} | Suspicious-screening score: ${row.suspicious_probability}%`;
}

loadHistory();
loadLatestSensorReading();
setInterval(() => { loadHistory(); loadLatestSensorReading(); }, 5000);
