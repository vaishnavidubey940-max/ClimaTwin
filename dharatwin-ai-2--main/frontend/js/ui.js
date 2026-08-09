window.ClimaUi = (() => {
  const notice = document.getElementById("notice");
  const setNotice = (message, kind = "info") => { notice.textContent = message; notice.dataset.kind = kind; };
  const value = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text ?? "N/A"; };
  const format = item => item === null || item === undefined ? "N/A" : String(item);
  function summary(observation) {
    const m = observation?.measurements || {};
    value("temperature-value", format(m.temperature)); value("rainfall-value", format(m.rainfall)); value("humidity-value", format(m.humidity));
    value("source-value", observation?.source || "N/A"); value("timestamp-value", observation?.timestamp || "No observation");
    const banner = document.getElementById("test-data-banner"); if (banner) banner.hidden = !(observation?.location?.name || "").toUpperCase().includes("TEST_DATA");
  }
  return { setNotice, value, summary };
})();
