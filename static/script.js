const form = document.getElementById('reading-form');
const resetBtn = document.getElementById('reset-btn');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  
  const sampleIdVal = document.getElementById('sample-id').value.trim();
  const phVal = document.getElementById('ph').value.trim();
  const tdsVal = document.getElementById('tds').value.trim();
  const tempVal = document.getElementById('temperature').value.trim();

  if (!sampleIdVal) {
    alert("Sample ID daalna zaroori hai!");
    document.getElementById('sample-id').focus();
    return;
  }

  if (!phVal || !tdsVal || !tempVal) {
    alert("Kripya saare sensor values bharein!");
    return;
  }

  const readings = {
    sample_id: sampleIdVal,
    ph: phVal,
    tds: tdsVal,
    temperature: tempVal
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

  const testTimeStr = new Date().toLocaleTimeString();
  
  updateDashboard({
    ...readings, 
    result: data.result, 
    suspicious_probability: data.suspicious_probability, 
    reason: data.reason,
    time: testTimeStr
  });

  // Table me real-time naya test record add karo jisme per-row PDF action button ho
  appendRecentTestRow({
    sample_id: data.sample_id,
    ph: data.ph,
    tds: data.tds,
    temperature: data.temperature,
    result: data.result,
    suspicious_probability: data.suspicious_probability,
    time: testTimeStr
  });

  showQR(data);
});

if (resetBtn) {
  resetBtn.addEventListener('click', () => {
    document.getElementById('sample-id').value = '';
    document.getElementById('ph').value = '';
    document.getElementById('tds').value = '';
    document.getElementById('temperature').value = '';

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
    const printBtn = document.getElementById('print-cert-btn');

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
    if (printBtn) {
      printBtn.disabled = true;
    }
    document.getElementById('qr-sample').textContent = 'Run a test to generate an audit report & QR certificate.';
  });
}

function appendRecentTestRow(record) {
  const tbody = document.getElementById('history-tbody');
  const emptyRow = document.getElementById('empty-history-row');
  if (emptyRow) {
    emptyRow.remove();
  }

  const isPass = record.result === 'NORMAL';
  const badgeClass = isPass ? 'badge-pass' : 'badge-fail';
  const badgeText = isPass ? 'PURE MILK' : 'SUSPICIOUS';

  const phVal = Number(record.ph).toFixed(2);
  const tdsVal = Math.round(record.tds);
  const tempVal = Number(record.temperature).toFixed(1);
  const riskVal = record.suspicious_probability;
  const timeVal = record.time || 'Just now';

  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><strong>${record.sample_id}</strong></td>
    <td>${phVal}</td>
    <td>${tdsVal}</td>
    <td>${tempVal}°C</td>
    <td><span class="history-badge ${badgeClass}">${badgeText}</span></td>
    <td><strong>${riskVal}%</strong></td>
    <td style="color:#64748b; font-size:0.82rem;">${timeVal}</td>
    <td style="text-align: center;">
      <button type="button" class="btn-row-pdf" onclick="printSingleRowPDF('${record.sample_id}', ${phVal}, ${tdsVal}, ${tempVal}, '${record.result}', ${riskVal}, '${timeVal}')">
        📄 PDF
      </button>
    </td>
  `;

  tbody.insertBefore(tr, tbody.firstChild);

  if (tbody.children.length > 10) {
    tbody.removeChild(tbody.lastChild);
  }
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
      appendRecentTestRow(row);
    }
  } catch (err) {}
}

function updateDashboard(row) {
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
  const printBtn = document.getElementById('print-cert-btn');
  
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
  if (printBtn) {
    printBtn.disabled = false;
  }
}

loadLatestSensorReading();
setInterval(loadLatestSensorReading, 120000);
