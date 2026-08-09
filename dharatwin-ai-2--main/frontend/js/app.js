(() => {
  let selectedId = null, features = [];
  const set = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value ?? "—"; };
  async function loadHistory() { if (!selectedId) return; try { const data = await ClimaApi.history(selectedId, "", ""); ClimaCharts.render(data.observations || []); } catch (error) { ClimaUi.setNotice(error.message, "error"); } }
  async function selectLocation(id) {
    selectedId = id; const feature = features.find(item => item.properties.location_id === Number(id));
    if (feature) { ClimaMap.focus(feature.geometry.coordinates[1], feature.geometry.coordinates[0]); ClimaTwin3D.setLocation(feature.geometry.coordinates[1], feature.geometry.coordinates[0]); }
    try {
      const latest = await ClimaApi.latest(id), m = latest.measurements || {};
      ClimaUi.summary(latest); set("feels-value", m.temperature ?? "—"); set("twin-temp", m.temperature == null ? "—" : `${m.temperature} °C`); set("twin-rain", m.rainfall == null ? "—" : `${m.rainfall} mm`); set("twin-humidity", m.humidity == null ? "—" : `${m.humidity}%`); set("twin-location", `(${latest.location?.name || latest.location?.state || "Selected location"})`); set("twin-source", latest.source || "LOCAL");
      const twin = await ClimaApi.twin(id), quality = twin.quality || {}, freshness = twin.data_status?.freshness || {};
      set("twin-observed", twin.observed_state ? "AVAILABLE" : "Unavailable"); set("twin-predicted", twin.predicted_state ? "AVAILABLE" : "Unavailable"); set("twin-quality", quality.status || "Unknown"); set("twin-health-status", quality.status ? String(quality.status).toUpperCase() : (twin.observed_state ? "HEALTHY" : "UNAVAILABLE")); set("health-label", quality.status || "Status"); set("health-score", quality.status ? "✓" : "—"); set("twin-freshness", freshness.status || "UNKNOWN"); set("twin-status", `Mode: ${twin.data_status?.mode || "LOCAL"}`);
      try {
        const pred = await ClimaApi.predict(id), preds = pred.predictions || {};
        if (preds.temperature) { set("predicted-temp", preds.temperature.prediction?.toFixed(1)); set("model-version", preds.temperature.model?.version ? "v" + preds.temperature.model.version.substring(0,10) : "RF Model"); }
        if (preds.rainfall) { set("predicted-rain", Math.max(0, preds.rainfall.prediction)?.toFixed(1)); }
      } catch (e) { /* Model may not be trained yet — leave defaults */ }
      await loadHistory(); ClimaUi.setNotice("Observed climate data loaded.");
    } catch (error) { ClimaUi.summary(null); ClimaUi.setNotice(error.message, "error"); }
  }
  async function refresh() {
    ClimaUi.setNotice("Loading climate workspace…");
    try {
      const [locations, geo, database, metrics, system, aiInfo] = await Promise.all([ClimaApi.locations(), ClimaApi.mapData(), ClimaApi.databaseStatus(), ClimaApi.metrics(), ClimaApi.systemStatus(), ClimaApi.aiStatus().catch(() => ({}))]);
      if (aiInfo.temperature?.status === "READY") { set("model-version", "RF v" + (aiInfo.temperature.model_version || "").substring(0, 10)); }
      features = geo.features || []; ClimaTwin3D.setClimatePoints(features); ClimaMap.render(features, document.getElementById("layer-select").value, selectLocation); const select = document.getElementById("location-select"); select.innerHTML = "";
      locations.locations.filter(x => x.latitude !== null && x.longitude !== null).forEach(x => { const option = document.createElement("option"); option.value = x.id; option.textContent = x.name || x.state || `${x.latitude}, ${x.longitude}`; select.appendChild(option); });
      if (select.options.length) { selectedId = selectedId || select.value; select.value = selectedId; await selectLocation(selectedId); } else { select.innerHTML = "<option>No mappable locations</option>"; ClimaUi.summary(null); }
      set("ingestion-value", database.last_ingestion ? new Date(database.last_ingestion).toLocaleDateString() : "No ingestion"); set("db-records", database.observations); set("db-locations", database.locations); set("updated-label", "Just now"); set("twin-updated", "Just now"); set("system-mode", system.data_mode); set("mode-label", system.data_mode); set("cmr-status", system.mosdac.replaceAll("_", " ")); set("meteo-status", system.imd.replaceAll("_", " ")); set("cmr-top", system.mosdac === "NOT_CONFIGURED" ? "Not Configured" : system.mosdac.replaceAll("_", " ")); set("meteo-top", system.imd === "NOT_CONFIGURED" ? "Not Configured" : system.imd.replaceAll("_", " ")); set("provider-status", `NASA CMR: ${system.mosdac} · Open-Meteo: ${system.imd} · Data mode: ${system.data_mode}`);
      const cmrEl = document.getElementById("cmr-top"); if (cmrEl) { cmrEl.className = system.mosdac === "NOT_CONFIGURED" ? "dot bad" : "dot good"; }
      const meteoEl = document.getElementById("meteo-top"); if (meteoEl) { meteoEl.className = system.imd === "NOT_CONFIGURED" ? "dot bad" : "dot good"; }
      const cmrSt = document.getElementById("cmr-status"); if (cmrSt) { cmrSt.className = system.mosdac === "NOT_CONFIGURED" ? "danger" : ""; }
      const meteoSt = document.getElementById("meteo-status"); if (meteoSt) { meteoSt.className = system.imd === "NOT_CONFIGURED" ? "danger" : ""; }
    } catch (error) { ClimaUi.summary(null); ClimaUi.setNotice(`Backend unavailable: ${error.message}`, "error"); }
  }
  async function runScenario() { if (!selectedId) return; const notice = document.getElementById("scenario-notice"); notice.textContent = "Running experimental scenario…"; try { const result = await ClimaApi.scenario(selectedId, { temperature_delta: Number(document.getElementById("scenario-temperature").value), rainfall_change_percent: Number(document.getElementById("scenario-rainfall").value), humidity_delta: Number(document.getElementById("scenario-humidity").value) }); const m = result.comparison; set("scenario-baseline", `T ${m.temperature?.baseline ?? "N/A"} · R ${m.rainfall?.baseline ?? "N/A"}`); set("scenario-result", `T ${m.temperature?.scenario ?? "N/A"} · R ${m.rainfall?.scenario ?? "N/A"}`); notice.textContent = result.disclaimer; } catch (error) { notice.textContent = error.message; } }
  function resetScenario() { ["temperature", "rainfall", "humidity"].forEach(name => { const input = document.getElementById(`scenario-${name}`); if (input) input.value = 0; const output = document.getElementById(`${name === "temperature" ? "temp" : name}-output`); if (output) output.textContent = name === "temperature" ? "0°C" : "0%"; }); set("scenario-baseline", "N/A"); set("scenario-result", "N/A"); document.getElementById("scenario-notice").textContent = "Scenario reset to baseline."; }
  document.addEventListener("DOMContentLoaded", () => { ClimaTwin3D.init(); ClimaMap.init(); document.getElementById("scenario-run").addEventListener("click", runScenario); document.getElementById("scenario-reset").addEventListener("click", resetScenario); document.getElementById("layer-select").addEventListener("change", e => ClimaMap.render(features, e.target.value, selectLocation)); document.getElementById("location-select").addEventListener("change", e => selectLocation(e.target.value)); ["temperature", "rainfall", "humidity"].forEach(name => { const input = document.getElementById(`scenario-${name}`), output = document.getElementById(`${name === "temperature" ? "temp" : name}-output`); if (input && output) input.addEventListener("input", () => { output.textContent = `${input.value}${name === "temperature" ? "°C" : "%"}`; }); }); refresh(); });
})();
