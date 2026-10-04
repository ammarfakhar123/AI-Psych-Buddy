// Draws the mood trend line chart. The canvas carries its data URL in `data-url`.
(function () {
  var canvas = document.getElementById('moodChart');
  if (!canvas || typeof Chart === 'undefined') { return; }
  var chart = null;

  function load(url) {
    fetch(url, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (chart) { chart.destroy(); }
        if (!data.labels.length) {
          var ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.font = '14px Nunito, sans-serif'; ctx.fillStyle = '#718096'; ctx.textAlign = 'center';
          ctx.fillText('No mood entries in this period yet.', canvas.width / 2, canvas.height / 2);
          return;
        }
        chart = new Chart(canvas, {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: [{
              label: 'Mood score', data: data.scores, borderColor: '#5b8def', backgroundColor: 'rgba(91,141,239,0.15)',
              fill: true, tension: 0.35, pointRadius: 5, pointBackgroundColor: '#4fb8a3'
            }]
          },
          options: {
            maintainAspectRatio: false,
            scales: { y: { min: 1, max: 5, ticks: { stepSize: 1 }, title: { display: true, text: '1 = low, 5 = good' } } },
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: function (c) { return data.moods[c.dataIndex] + ' (' + c.parsed.y + '/5)'; } } }
            }
          }
        });
      })
      .catch(function () { /* chart is optional; fail silently */ });
  }

  load(canvas.dataset.url);

  document.querySelectorAll('[data-chart-range]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('[data-chart-range]').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      load(btn.dataset.chartUrl);
    });
  });
})();
