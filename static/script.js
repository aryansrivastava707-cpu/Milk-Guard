const form = document.getElementById('reading-form');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const readings = {
    sample_id: document.getElementById('sample-id').value,
    ph: document.getElementById('ph').value,
    tds: document.getElementById('tds').value,
    temperature: document.getElementById('temperature').value
  };
  const response = await fetch('/predict', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(readings)});
  const data = await response.json();
  if (!response.ok) { alert(data.error); return; }
  const result = document.getElementById('result');
  const status = document.getElementById('status');
  updateDashboard({...readings, result: data.result, suspicious_probability: data.suspicious_probability, time: 'Manual test'});
  showQR(data);
});

async function loadLatestSensorReading() {
  const response = await fetch('/latest');
  const row = await response.json();
  if (!row) return;
  // An ESP32 posts through /predict; use the saved latest result to update the page.
  updateDashboard(row);
}

function updateDashboard(row) {
  document.getElementById('ph').value = row.ph;
  document.getElementById('tds').value = row.tds;
  document.getElementById('temperature').value = row.temperature;
  document.getElementById('current-ph').textContent = Number(row.ph).toFixed(2);
  document.getElementById('current-tds').textContent = Math.round(row.tds);
  document.getElementById('current-temperature').textContent = `${Number(row.temperature).toFixed(1)}°`;
  const suspicious = row.result === 'SUSPICIOUS';
  const score = Number(row.suspicious_probability);
  const status = document.getElementById('status');
  status.textContent = suspicious ? '⚠ SUSPICIOUS' : '✓ NORMAL';
  status.className = suspicious ? 'suspicious' : 'normal';
  document.getElementById('quality-symbol').textContent = suspicious ? '!' : '✓';
  document.getElementById('quality-symbol').style.background = suspicious ? '#c56727' : '#218454';
  document.getElementById('probability').textContent = `Latest reading: ${row.time} · Screening result based on three sensor values.`;
  document.getElementById('score-value').textContent = `${score}%`;
  const bar = document.getElementById('score-bar');
  bar.style.width = `${score}%`;
  bar.style.background = suspicious ? '#c56727' : '#2a9158';
}

function showQR(data) {
  if (!data.report_url) return;
  document.getElementById('qr-card').classList.remove('hidden');
  document.getElementById('qr-sample').textContent = `Sample ID: ${data.sample_id}`;
  const link = document.getElementById('report-link');
  link.href = data.report_url;
  document.getElementById('qr-image').src = `https://api.qrserver.com/v1/create-qr-code/?size=170x170&data=${encodeURIComponent(data.report_url)}`;
}

loadLatestSensorReading();
setInterval(loadLatestSensorReading, 5000);
