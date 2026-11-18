const defaultChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#94a3b8' } } },
  scales: {
    x: { ticks: { color: '#64748b' }, grid: { color: '#334155' } },
    y: { ticks: { color: '#64748b' }, grid: { color: '#334155' } }
  }
};

function createLineChart(canvasId, label, color, data = [], labels = []) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: color,
        backgroundColor: color + '20',
        tension: 0.4,
        pointRadius: 3,
        fill: true
      }]
    },
    options: { ...defaultChartOptions }
  });
}

function updateChart(chart, data, labels) {
  chart.data.labels = labels;
  chart.data.datasets[0].data = data;
  chart.update();
}
