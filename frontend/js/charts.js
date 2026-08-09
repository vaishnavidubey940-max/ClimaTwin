window.ClimaCharts = (() => {
  const charts = {};
  const palette = { temperature: "#38dc63", rainfall: "#3896ff", humidity: "#32d4bb" };
  function renderChart(id, history, key, label, color) {
    const canvas = document.getElementById(id); if (!canvas || !window.Chart) return;
    if (charts[id]) charts[id].destroy();
    const values = (history || []).filter(row => row.measurements && row.measurements[key] !== null && row.measurements[key] !== undefined);
    charts[id] = new Chart(canvas, { type: key === "rainfall" ? "bar" : "line", data: { labels: values.map(row => new Date(row.timestamp).toLocaleDateString()), datasets: [{ label, data: values.map(row => row.measurements[key]), borderColor: color, backgroundColor: `${color}55`, borderWidth: 2, pointRadius: values.length > 20 ? 1 : 3, tension: .35, fill: key !== "rainfall" }] }, options: { responsive: true, maintainAspectRatio: false, animation: { duration: 450 }, scales: { x: { grid: { color: "#1a334455" }, ticks: { color: "#8fa8bb", maxTicksLimit: 6 } }, y: { grid: { color: "#1a334455" }, ticks: { color: "#8fa8bb" }, title: { display: true, text: label, color: "#9eb6c5" } } }, plugins: { legend: { labels: { color: "#d8e9f2", boxWidth: 10 } } } } });
    return values.length;
  }
  function emptyState(id, show) { const el = document.getElementById(id); if (el) el.style.display = show ? "block" : "none"; }
  function render(history) { const rows = history || []; const tempCount = renderChart("temperature-chart", rows, "temperature", "Observed temperature (°C)", palette.temperature) || 0; const rainCount = renderChart("rainfall-chart", rows, "rainfall", "Observed rainfall (mm)", palette.rainfall) || 0; renderChart("history-chart", rows, "temperature", "Historical temperature (°C)", "#4ab4ff"); emptyState("temperature-empty", !tempCount); emptyState("rainfall-empty", !rainCount); }
  return { render };
})();
