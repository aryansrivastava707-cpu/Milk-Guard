const form = document.getElementById('reading-form');
const resetBtn = document.getElementById('reset-btn');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const readings = {
    sample_id: document.getElementById('sample-id').value,
    ph: document.getElementById('ph').value,
    tds: document.getElementById('tds').value,
    temperature: document.getElementById('temperature').value
  };
  const response = await fetch('/predict', {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'}, 
    body: JSON.stringify(readings)
  });
  const data = await response.json();
  if (!response.ok) { 
    alert(data.error); 
    return; 
  }
  updateDashboard({
    ...readings, 
    result: data.result, 
    suspicious_probability: data.suspicious_probability, 
    reason: data.reason,
    time: 'Manual test'
  });
  showQR(data);
});

if (resetBtn) {
  resetBtn.addEventListener('click', () => {
    document.getElementById('sample-id').value = '';
    document.getElementById('ph').value = '6.65';
    document.getElementById('tds').value = '310';
    document.getElementById('temperature').value = '27';

    document.getElementById('current-ph').textContent = '--';
    document.getElementById('current-tds').textContent = '--';
    document.getElementById('current-temperature').textContent = '--';

    const status = document.getElementById('status');
    status.textContent = 'Waiting for sensor data';
    status.className = '';
    status.style.color = '';

    const symbol = document.getElementById('quality-symbol');
    symbol.textContent = '?';
    symbol.style.background = '';
    symbol.style.color = '';

    const prob = document.getElementById('probability');
    prob.textContent = 'Connect the ESP32 or run a manual test to begin screening.';
    prob.style.color = '';

    document.getElementById('score-value').textContent = '--';
    const bar = document.getElementById('score-bar');
    bar.style.width = '0%';
    bar.style.background = '';

    const qrPlaceholder = document.getElementById('qr-placeholder');
    const qrImage = document.getElementById('qr-image');
    const link = document.getElementById('report-link');
    const downloadBtn = document.getElementById('download-qr-btn');

    if (qrPlaceholder) qrPlaceholder.style.display = 'flex';
    if (qrImage) {
      qrImage.style.display = 'none';
      qrImage.src = '';
    }
    if (link) {
      link.style.display = 'none';
      link.href = '';
    }
    if (downloadBtn) {
      downloadBtn.disabled = true;
    }
    document.getElementById('qr-sample').textContent = 'Run a test to generate an audit report & QR certificate.';
  });
}

async function loadLatestSensorReading() {
  try {
    const response = await fetch('/latest');
    const row = await response.json();
    if (!row) return;
    updateDashboard(row);
    if (row.test_id) {
      showQR({
        sample_id: row.sample_id,
        report_url: `${window.location.origin}/report/${row.test_id}`
      });
    }
  } catch (err) {}
}

function updateDashboard(row) {
  if (row.ph !== undefined) document.getElementById('ph').value = row.ph;
  if (row.tds !== undefined) document.getElementById('tds').value = row.tds;
  if (row.temperature !== undefined) document.getElementById('temperature').value = row.temperature;
  
  if (row.ph !== undefined) document.getElementById('current-ph').textContent = Number(row.ph).toFixed(2);
  if (row.tds !== undefined) document.getElementById('current-tds').textContent = Math.round(row.tds);
  if (row.temperature !== undefined) document.getElementById('current-temperature').textContent = `${Number(row.temperature).toFixed(1)}°`;
  
  const suspicious = row.result === 'SUSPICIOUS';
  const score = Number(row.suspicious_probability || 0);
  const status = document.getElementById('status');
  
  status.textContent = suspicious ? 'SUSPICIOUS' : 'PURE MILK';
  status.className = suspicious ? 'suspicious' : 'normal';
  status.style.color = suspicious ? '#d90429' : '#2b9348';
  
  const symbol = document.getElementById('quality-symbol');
  symbol.textContent = suspicious ? '!' : '✓';
  symbol.style.background = suspicious ? '#c56727' : '#218454';
  
  const prob = document.getElementById('probability');
  prob.innerHTML = `<strong>Reason:</strong> ${row.reason || (suspicious ? 'Abnormal sensor values detected.' : 'Standard milk quality verified.')}`;
  prob.style.color = suspicious ? '#b7094c' : '#2b9348';
  
  document.getElementById('score-value').textContent = `${score}% Risk`;
  const bar = document.getElementById('score-bar');
  bar.style.width = `${score}%`;
  bar.style.background = suspicious ? '#d90429' : '#2b9348';
}

function showQR(data) {
  if (!data.report_url) return;
  
  const qrPlaceholder = document.getElementById('qr-placeholder');
  const qrImage = document.getElementById('qr-image');
  const link = document.getElementById('report-link');
  const downloadBtn = document.getElementById('download-qr-btn');
  
  if (qrPlaceholder) qrPlaceholder.style.display = 'none';
  if (qrImage) {
    qrImage.style.display = 'block';
    qrImage.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(data.report_url)}`;
  }
  
  document.getElementById('qr-sample').textContent = `Sample: ${data.sample_id || '--'}`;
  
  if (link) {
    link.style.display = 'inline-block';
    link.href = data.report_url;
  }
  if (downloadBtn) {
    downloadBtn.disabled = false;
  }
}

loadLatestSensorReading();
setInterval(loadLatestSensorReading, 120000);
