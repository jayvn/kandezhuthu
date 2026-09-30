let map;
let activeTool = "pin";
let currentMarker = null;
let currentPolygon = null;
let currentRoadLine = null;
let polygonPoints = [];
let roadPoints = [];
let vertexMarkers = [];
let dimensionLabels = [];

let googleHybridLayer, googleSatelliteLayer, googleRoadsLayer, googleTerrainLayer, osmLayer;

const KERALA_PRESETS = {
  aluva: { name: "Aluva (Periyar River Basin - 2018 Flood Zone)", lat: 10.1076, lng: 76.3516, zoom: 17, cents: 10.0, roadWidth: 3.2, surveyNo: "345/1", village: "Aluva West", desc: "10 Cents residential plot near Periyar river basin" },
  kakkanad: { name: "Kakkanad / Infopark (Elevated Midlands)", lat: 10.0159, lng: 76.3419, zoom: 18, cents: 6.5, roadWidth: 4.5, surveyNo: "182/4", village: "Kakkanad", desc: "6.5 Cents elevated IT corridor plot with wide 4.5m access road" },
  kuttanad: { name: "Kuttanad (Sub-Sea-Level Wetland Polders)", lat: 9.4981, lng: 76.4312, zoom: 17, cents: 18.0, roadWidth: 2.0, surveyNo: "88/2", village: "Kuttanad", desc: "18 Cents agrarian polder with canal frontage" },
  chengannur: { name: "Chengannur (Pamba River Flood Corridor)", lat: 9.3175, lng: 76.6173, zoom: 17, cents: 8.5, roadWidth: 3.0, surveyNo: "214/5", village: "Chengannur", desc: "8.5 Cents riverbank valley plot" },
  angamaly: { name: "Angamaly (Paddy & Agricultural Zone)", lat: 10.1960, lng: 76.3860, zoom: 17, cents: 22.0, roadWidth: 3.0, surveyNo: "412/1", village: "Angamaly", desc: "22 Cents suburban parcel on paddy boundary" },
  kaloor: { name: "Kaloor / Kochi (High Density Coastal)", lat: 9.9937, lng: 76.2922, zoom: 18, cents: 4.8, roadWidth: 5.5, surveyNo: "95/3", village: "Kanayannur", desc: "4.8 Cents high-density urban city plot" },
  thrissur: { name: "Thrissur (Swaraj Round & Kole Wetlands)", lat: 10.5276, lng: 76.2144, zoom: 17, cents: 12.0, roadWidth: 3.8, surveyNo: "55/2", village: "Thrissur", desc: "12 Cents commercial-residential mix parcel" },
  kottayam: { name: "Kottayam (Meenachil Wetland Valley)", lat: 9.5916, lng: 76.5222, zoom: 17, cents: 14.5, roadWidth: 2.8, surveyNo: "302/1", village: "Kottayam", desc: "14.5 Cents rubber estate margin plot" },
  kozhikode: { name: "Kozhikode (Coastal City)", lat: 11.2588, lng: 75.7804, zoom: 17, cents: 7.2, roadWidth: 3.5, surveyNo: "118/4", village: "Kozhikode", desc: "7.2 Cents coastal residential plot" },
  trivandrum: { name: "Thiruvananthapuram (Kazhakkoottam)", lat: 8.5686, lng: 76.8731, zoom: 17, cents: 5.5, roadWidth: 4.2, surveyNo: "440/2", village: "Kazhakkoottam", desc: "5.5 Cents Technopark corridor villa plot" }
};

function initMap() {
  if (typeof L === "undefined") {
    const mv = document.getElementById("map-view");
    if (mv) mv.innerHTML = '<div class="map-unavailable">Map could not load. Check your connection and reload.</div>';
    return;
  }
  const googleTileSubdomains = ['mt0', 'mt1', 'mt2', 'mt3'];
  
  googleHybridLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
    maxZoom: 21,
    subdomains: googleTileSubdomains,
    attribution: '&copy; Google Maps Satellite'
  });

  googleSatelliteLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
    maxZoom: 21,
    subdomains: googleTileSubdomains,
    attribution: '&copy; Google Maps Satellite'
  });

  googleRoadsLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
    maxZoom: 21,
    subdomains: googleTileSubdomains,
    attribution: '&copy; Google Maps'
  });

  googleTerrainLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}', {
    maxZoom: 20,
    subdomains: googleTileSubdomains,
    attribution: '&copy; Google Maps Terrain'
  });

  osmLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  });

  map = L.map('map-view', {
    center: [10.3, 76.4],
    zoom: 8,
    layers: [googleHybridLayer]
  });

  map.on('click', handleMapClick);

  fetchConfig();
}

async function fetchConfig() {
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    if (data.google_maps_api_key) {
      console.log("[Kandezhuthu UI] Google Maps API key available");
    }
  } catch (e) {}
}

function switchMapLayer(layerKey) {
  [googleHybridLayer, googleSatelliteLayer, googleRoadsLayer, googleTerrainLayer, osmLayer].forEach(l => {
    if (map.hasLayer(l)) map.removeLayer(l);
  });

  switch(layerKey) {
    case 'google-hybrid': map.addLayer(googleHybridLayer); break;
    case 'google-satellite': map.addLayer(googleSatelliteLayer); break;
    case 'google-roads': map.addLayer(googleRoadsLayer); break;
    case 'google-terrain': map.addLayer(googleTerrainLayer); break;
    case 'osm': map.addLayer(osmLayer); break;
  }
}

function setMapTool(toolName) {
  activeTool = toolName;
  document.querySelectorAll(".map-tool-btn").forEach(btn => {
    btn.classList.toggle("active", btn.id === "tool-" + toolName);
  });

  if (toolName === "plot") {
    polygonPoints = [];
    clearVertexMarkers();
    clearDimensionLabels();
    if (currentPolygon) { map.removeLayer(currentPolygon); currentPolygon = null; }
  } else if (toolName === "road") {
    roadPoints = [];
    clearDimensionLabels();
    if (currentRoadLine) { map.removeLayer(currentRoadLine); currentRoadLine = null; }
  }

  updateGuidanceBarText();
  updateUndoState();
}

function handleMapClick(e) {
  const { lat, lng } = e.latlng;

  if (activeTool === "pin") {
    setPin(lat, lng);
  } else if (activeTool === "plot") {
    addPlotVertex(lat, lng);
  } else if (activeTool === "road") {
    addRoadPoint(lat, lng);
  }
}

function setPin(lat, lng) {
  if (currentMarker) map.removeLayer(currentMarker);

  currentMarker = L.marker([lat, lng], {
    title: "Inspected Plot Pin",
    riseOnHover: true
  }).addTo(map);

  currentMarker.bindPopup(`<b>${currentLanguage === "ml" ? "നിങ്ങളുടെ പ്ലോട്ട്" : "Your plot"}</b><br>Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}<br><button onclick="openAutoDemarcateModal()" style="margin-top:6px; font-size: var(--fs-12); padding:4px 10px; background:#990f3d; color:#fff; border:none; border-radius:4px; cursor:pointer; font-weight:600;">${currentLanguage === "ml" ? "അതിർത്തി കണ്ടെത്തുക" : "Auto-outline here"}</button>`).openPopup();
  updateHUDLocation(lat, lng);

  const coordsEl = document.getElementById("detect-modal-coords");
  if (coordsEl) {
    coordsEl.textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  }
}

function addPlotVertex(lat, lng) {
  polygonPoints.push(L.latLng(lat, lng));

  const vertexIndex = polygonPoints.length;
  const kalluIcon = L.divIcon({
    className: 'custom-kallu-marker',
    html: `<div style="width:14px; height:14px; background:#0d7680; border:2.5px solid #990f3d; border-radius:50%; box-shadow:0 1px 4px rgba(0,0,0,0.45); cursor:grab;" title="Corner Stone #${vertexIndex} (Survey Kallu) - Drag to adjust"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });

  const vertexMarker = L.marker([lat, lng], {
    icon: kalluIcon,
    draggable: true,
    riseOnHover: true
  }).addTo(map);
  
  vertexMarker.bindTooltip(`Kallu #${vertexIndex} (Drag to move)`, { permanent: false, direction: 'top' });

  // Real-time FMB edge dimensions and area recalculation on drag
  vertexMarker.on('drag', function(e) {
    const idx = vertexMarkers.indexOf(vertexMarker);
    if (idx !== -1) {
      polygonPoints[idx] = e.target.getLatLng();
      updatePlotDisplay();
    }
  });

  vertexMarker.on('dragend', function() {
    const idx = vertexMarkers.indexOf(vertexMarker);
    if (polygonPoints.length >= 3) {
      const areaSqM = calculatePolygonArea(polygonPoints);
      const cents = (areaSqM / 40.4686).toFixed(2);
      document.getElementById("guidance-text").textContent = `Corner Stone #${idx + 1} adjusted. Updated extent: ${cents} Cents.`;
    }
  });

  vertexMarkers.push(vertexMarker);

  // If clicking near the first point when >=3 points, seal plot
  if (polygonPoints.length >= 4 && calculateDistance(polygonPoints[0], L.latLng(lat, lng)) < 8) {
    polygonPoints.pop();
    map.removeLayer(vertexMarker);
    vertexMarkers.pop();
    finishPlot();
    return;
  }

  updatePlotDisplay();
  updateUndoState();
}

function updatePlotDisplay() {
  clearDimensionLabels();

  if (polygonPoints.length >= 2) {
    if (currentPolygon) map.removeLayer(currentPolygon);

    currentPolygon = L.polygon(polygonPoints, {
      color: "#990f3d",
      weight: 2.5,
      fillColor: "#0d7680",
      fillOpacity: 0.35,
      dashArray: polygonPoints.length === 2 ? "5, 5" : undefined
    }).addTo(map);

    // Calculate FMB segment dimensions
    for (let i = 0; i < polygonPoints.length; i++) {
      const nextIdx = (i + 1) % polygonPoints.length;
      if (polygonPoints.length === 2 && i === 1) break; // Don't close if only 2 points
      const p1 = polygonPoints[i];
      const p2 = polygonPoints[nextIdx];
      const distM = calculateDistance(p1, p2);
      const midLat = (p1.lat + p2.lat) / 2;
      const midLng = (p1.lng + p2.lng) / 2;

      const dimLabel = L.tooltip({
        permanent: true,
        direction: 'center',
        className: 'fmb-segment-label'
      })
      .setContent(`${distM.toFixed(1)}m`)
      .setLatLng([midLat, midLng])
      .addTo(map);

      dimensionLabels.push(dimLabel);
    }

    if (polygonPoints.length >= 3) {
      const areaSqM = calculatePolygonArea(polygonPoints);
      const cents = (areaSqM / 40.4686).toFixed(2);
      const ares = (areaSqM / 100).toFixed(2);
      const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
      const isMl = currentLanguage === "ml";

      document.getElementById("hud-cents").textContent = `${cents} ${t.hudCentsUnit}`;
      document.getElementById("hud-sqm").textContent = `${ares} ${t.hudAresUnit} (${areaSqM.toFixed(1)} ${t.hudSqMUnit})`;
      document.getElementById("guidance-text").textContent = isMl
        ? `പ്ലോട്ട് വരയ്ക്കുന്നു: ${polygonPoints.length} അതിർത്തിക്കല്ലുകൾ അടയാളപ്പെടുത്തി (${cents} സെന്റ്). 'പ്ലോട്ട് പൂർത്തിയാക്കുക' ക്ലിക്ക് ചെയ്യുക.`
        : `Plot in progress: ${polygonPoints.length} corner stones marked (${cents} Cents). Click 'Seal Plot' to finish.`;
    }
  }
}

function finishPlot() {
  if (polygonPoints.length < 3) {
    const isMl = currentLanguage === "ml";
    alert(isMl ? "പ്ലോട്ട് പൂർത്തിയാക്കാൻ കുറഞ്ഞത് 3 അതിർത്തിക്കല്ലുകൾ അടയാളപ്പെടുത്തുക." : "Please place at least 3 corner points to seal a plot boundary.");
    return;
  }
  updatePlotDisplay();
  const areaSqM = calculatePolygonArea(polygonPoints);
  const cents = (areaSqM / 40.4686).toFixed(2);
  const isMl = currentLanguage === "ml";
  document.getElementById("guidance-text").textContent = isMl
    ? `✓ പ്ലോട്ട് പൂർത്തിയായി! വിസ്തീർണ്ണം: ${cents} സെന്റ്. വിവരങ്ങൾ താഴെ കാണുക അല്ലെങ്കിൽ 'ഓഡിറ്ററിലേക്ക് അയക്കുക' ക്ലിക്ക് ചെയ്യുക.`
    : `✓ Plot sealed! Extent: ${cents} Cents. Review stats in HUD below or click 'Send Plot to Auditor AI'.`;
  
  let sumLat = 0, sumLng = 0;
  for (const pt of polygonPoints) { sumLat += pt.lat; sumLng += pt.lng; }
  const cLat = sumLat / polygonPoints.length;
  const cLng = sumLng / polygonPoints.length;
  updateHUDLocation(cLat, cLng, undefined, parseFloat(cents));

  setMapTool("pin");
}

function addRoadPoint(lat, lng) {
  roadPoints.push(L.latLng(lat, lng));

  const roadMarker = L.circleMarker([lat, lng], {
    radius: 5,
    color: "#990f3d",
    fillColor: "#990f3d",
    fillOpacity: 1
  }).addTo(map);
  vertexMarkers.push(roadMarker);

  const isMl = currentLanguage === "ml";
  const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;

  if (roadPoints.length === 1) {
    document.getElementById("guidance-text").textContent = isMl
      ? "വഴിയുടെ ഒരതിർത്തി അടയാളപ്പെടുത്തി! ഇനി എതിർവശത്തെ അതിർത്തിയിൽ ക്ലിക്ക് ചെയ്യുക."
      : "First road edge marked! Now click directly opposite across the road.";
  }

  if (roadPoints.length === 2) {
    if (currentRoadLine) map.removeLayer(currentRoadLine);

    currentRoadLine = L.polyline(roadPoints, {
      color: "#990f3d",
      weight: 4,
      dashArray: "6, 6"
    }).addTo(map);

    const distM = calculateDistance(roadPoints[0], roadPoints[1]);
    let statusBadgeClass = "pass";
    let statusBadgeText = t.hudRoadPass;
    let desc = "";

    if (distM >= 3.0) {
      statusBadgeClass = "pass";
      statusBadgeText = t.hudRoadPass;
      desc = isMl ? "വീടുപണിക്ക് അനുമതി ലഭ്യമാണ് (KPBR ചട്ടം)" : "Permit Eligible for Residential Construction";
    } else if (distM >= 1.2) {
      statusBadgeClass = "warn";
      statusBadgeText = t.hudRoadWarn;
      desc = isMl ? "ചെറിയ പ്ലോട്ടുകൾക്ക് മാത്രം (KPBR ചട്ടം 59)" : "Restricted built-up area under KPBR Rule 59";
    } else {
      statusBadgeClass = "fail";
      statusBadgeText = t.hudRoadFail;
      desc = isMl ? "വീടുപണിക്ക് അനുമതി ലഭിക്കില്ല (<1.2m)" : "Cannot get residential permit under Kerala Building Rules (<1.2m)";
    }

    document.getElementById("hud-road-text").textContent = `${distM.toFixed(1)} ${t.hudMetersUnit}`;
    const badgeEl = document.getElementById("hud-road-badge");
    badgeEl.className = `badge-road ${statusBadgeClass}`;
    badgeEl.textContent = statusBadgeText;

    const popupRoadLbl = isMl ? "വഴി വീതി:" : "Access Road Width:";
    const popupKpbrLbl = isMl ? "KPBR പദവി:" : "KPBR Status:";
    currentRoadLine.bindPopup(`<b>${popupRoadLbl}</b> ${distM.toFixed(1)} ${t.hudMetersUnit}<br><b>${popupKpbrLbl}</b> ${statusBadgeText}<br>${desc}`).openPopup();
    
    document.getElementById("guidance-text").textContent = isMl
      ? `വഴി അളന്നു: ${distM.toFixed(1)} ${t.hudMetersUnit}. ${statusBadgeText}`
      : `Road measured: ${distM.toFixed(1)}m. ${statusBadgeText}`;
    roadPoints = [];
  }

  updateUndoState();
}

function undoLastPoint() {
  const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;
  if (activeTool === "plot" && polygonPoints.length > 0) {
    polygonPoints.pop();
    if (vertexMarkers.length > 0) {
      map.removeLayer(vertexMarkers.pop());
    }
    if (polygonPoints.length >= 2) {
      updatePlotDisplay();
    } else {
      clearDimensionLabels();
      if (currentPolygon) { map.removeLayer(currentPolygon); currentPolygon = null; }
      document.getElementById("hud-cents").textContent = `0.00 ${t.hudCentsUnit}`;
      document.getElementById("hud-sqm").textContent = `0.0 ${t.hudAresUnit} (0.0 ${t.hudSqMUnit})`;
    }
  } else if (activeTool === "road" && roadPoints.length > 0) {
    roadPoints.pop();
    if (vertexMarkers.length > 0) {
      map.removeLayer(vertexMarkers.pop());
    }
  }
  updateUndoState();
}

function updateUndoState() {
  const btn = document.getElementById("guidance-undo-btn");
  if (!btn) return;
  if (activeTool === "plot") {
    btn.disabled = polygonPoints.length === 0;
  } else if (activeTool === "road") {
    btn.disabled = roadPoints.length === 0;
  } else {
    btn.disabled = true;
  }
}

function clearMapDrawings() {
  if (currentMarker) { map.removeLayer(currentMarker); currentMarker = null; }
  if (currentPolygon) { map.removeLayer(currentPolygon); currentPolygon = null; }
  if (currentRoadLine) { map.removeLayer(currentRoadLine); currentRoadLine = null; }
  clearVertexMarkers();
  clearDimensionLabels();
  polygonPoints = [];
  roadPoints = [];
  
  document.getElementById("hud-cents").textContent = "0.00 Cents";
  document.getElementById("hud-sqm").textContent = "0.0 Ares (0.0 m²)";
  document.getElementById("hud-road-text").textContent = "Not Measured";
  const badgeEl = document.getElementById("hud-road-badge");
  badgeEl.className = "badge-road";
  badgeEl.textContent = "No Road Measured";
  updateUndoState();
}

function clearVertexMarkers() {
  vertexMarkers.forEach(m => map.removeLayer(m));
  vertexMarkers = [];
}

function clearDimensionLabels() {
  dimensionLabels.forEach(l => map.removeLayer(l));
  dimensionLabels = [];
}

/* Calibrated Plot Extent Footprint Generator */
function generateCalibratedFootprint(lat, lng, cents = 10.0, aspectRatio = "1:1") {
  const areaSqM = cents * 40.4686;
  let ratio = 1.0;
  if (aspectRatio === "1:1.5") ratio = 1.5;
  else if (aspectRatio === "1.5:1") ratio = 0.667;
  else if (aspectRatio === "1:2") ratio = 2.0;

  const hMeters = Math.sqrt(areaSqM / ratio);
  const wMeters = hMeters * ratio;

  const latDegPerMeter = 1.0 / 111320;
  const lngDegPerMeter = 1.0 / (111320 * Math.cos(lat * Math.PI / 180));

  const dLat = (hMeters * latDegPerMeter);
  const dLng = (wMeters * lngDegPerMeter);

  return [
    [lat - dLat/2, lng - dLng/2],
    [lat + dLat/2, lng - dLng/2],
    [lat + dLat/2, lng + dLng/2],
    [lat - dLat/2, lng + dLng/2]
  ];
}

/* Universal Boundary Application Engine */
function applyPlotPolygon(coords, meta = {}) {
  clearMapDrawings();

  if (!coords || coords.length < 3) {
    console.error("Invalid polygon coords", coords);
    return;
  }

  polygonPoints = coords.map(c => L.latLng(c[0], c[1]));

  // Draggable Kallu markers
  polygonPoints.forEach((pt, idx) => {
    const kalluIcon = L.divIcon({
      className: 'custom-kallu-marker',
      html: `<div style="width:14px; height:14px; background:#0d7680; border:2.5px solid #990f3d; border-radius:50%; box-shadow:0 1px 4px rgba(0,0,0,0.45); cursor:grab;" title="Corner Stone #${idx + 1} (Survey Kallu) - Drag to adjust"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });
    const vm = L.marker(pt, { icon: kalluIcon, draggable: true, riseOnHover: true }).addTo(map);
    vm.bindTooltip(`Kallu #${idx + 1} (Drag to move)`, { permanent: false, direction: 'top' });
    vm.on('drag', function(e) {
      const mIdx = vertexMarkers.indexOf(vm);
      if (mIdx !== -1) {
        polygonPoints[mIdx] = e.target.getLatLng();
        updatePlotDisplay();
      }
    });
    vm.on('dragend', function() {
      const areaSqM = calculatePolygonArea(polygonPoints);
      const cents = (areaSqM / 40.4686).toFixed(2);
      document.getElementById("hud-cents").textContent = `${cents} Cents`;
      document.getElementById("guidance-text").textContent = `Corner Stone #${idx + 1} adjusted. Updated extent: ${cents} Cents.`;
    });
    vertexMarkers.push(vm);
  });

  updatePlotDisplay();

  // Compute centroid
  let sumLat = 0, sumLng = 0;
  polygonPoints.forEach(p => { sumLat += p.lat; sumLng += p.lng; });
  const centerLat = sumLat / polygonPoints.length;
  const centerLng = sumLng / polygonPoints.length;

  const actualAreaSqM = calculatePolygonArea(polygonPoints);
  const actualCents = meta.extentCents || parseFloat((actualAreaSqM / 40.4686).toFixed(2));
  const isMl = currentLanguage === "ml";
  const title = meta.title || (isMl ? "അടയാളപ്പെടുത്തിയ പ്ലോട്ട്" : "Demarcated Plot");
  const sy = meta.surveyNo || (isMl ? "റീ-സർവേ പ്ലോട്ട്" : "Re-Sy Plot");
  const village = meta.village || (isMl ? "കേരള വില്ലേജ്" : "Kerala Village");
  const syLbl = isMl ? "സർവേ നമ്പർ:" : "Survey:";
  const extLbl = isMl ? "വിസ്തീർണ്ണം:" : "Extent:";
  const centsUnit = isMl ? "സെന്റ്" : "Cents";
  const defaultSource = isMl ? "✓ അടയാളപ്പെടുത്തിയ അതിർത്തി" : "✓ Demarcated Boundary";

  currentMarker = L.marker([centerLat, centerLng], { riseOnHover: true }).addTo(map);
  currentMarker.bindPopup(`
    <b>${title}</b><br>
    ${syLbl} <strong>${sy}</strong> (${village})<br>
    ${extLbl} <strong>${actualCents} ${centsUnit}</strong> (${(actualCents * 40.4686).toFixed(1)} m²)<br>
    <small style="color:#990f3d; font-weight:600;">${meta.source ? '✓ ' + meta.source : defaultSource}</small>
  `).openPopup();

  // Road indicator if roadWidth is known
  if (meta.roadWidth) {
    const p1 = polygonPoints[0];
    const roadStart = L.latLng(p1.lat, p1.lng - 0.00003);
    const roadEnd = L.latLng(p1.lat, p1.lng);
    currentRoadLine = L.polyline([roadStart, roadEnd], {
      color: "#990f3d",
      weight: 3.5,
      dashArray: "4, 4"
    }).addTo(map);
  }

  updateHUDLocation(centerLat, centerLng, `${village} (${title})`, actualCents, meta.roadWidth);

  if (currentPolygon) {
    map.fitBounds(currentPolygon.getBounds().pad(0.3));
  }

  document.getElementById("guidance-icon").textContent = "◆";
  document.getElementById("guidance-text").textContent = isMl
    ? `${actualCents} സെന്റ് അതിർത്തി അടയാളപ്പെടുത്തി (${title}). അതിരുകൾ മാറ്റാൻ പച്ച അതിർത്തിക്കല്ലുകൾ നീക്കുക.`
    : `Demarcated ${actualCents} Cents (${title}). Drag green corner stones to adjust boundary.`;
}

function applyLocationPreset(presetKey) {
  if (!presetKey || !KERALA_PRESETS[presetKey]) return;
  const p = KERALA_PRESETS[presetKey];
  map.setView([p.lat, p.lng], p.zoom);
  setPin(p.lat, p.lng);
}

/* Auto-Demarcate Modal Controls */
function openAutoDemarcateModal() {
  const modal = document.getElementById("auto-demarcate-modal");
  if (!modal) return;
  
  let targetLat = 10.1076, targetLng = 76.3516;
  if (currentMarker) {
    const pos = currentMarker.getLatLng();
    targetLat = pos.lat;
    targetLng = pos.lng;
  } else if (map) {
    const center = map.getCenter();
    targetLat = center.lat;
    targetLng = center.lng;
  }
  const coordsEl = document.getElementById("detect-modal-coords");
  if (coordsEl) coordsEl.textContent = `${targetLat.toFixed(5)}, ${targetLng.toFixed(5)}`;

  modal.style.display = "flex";
}

function closeAutoDemarcateModal() {
  const modal = document.getElementById("auto-demarcate-modal");
  if (modal) modal.style.display = "none";
}

function switchDemarcateTab(tabName) {
  const tabs = ['detect', 'extent', 'cadastral', 'import'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const pane = document.getElementById(`pane-${t}`);
    if (btn) btn.classList.toggle('active', t === tabName);
    if (pane) pane.style.display = (t === tabName) ? 'block' : 'none';
  });
}

function setExtentInput(cents) {
  const inp = document.getElementById("custom-extent-input");
  if (inp) inp.value = cents;
  updateExtentSqmDisplay(cents);
  document.querySelectorAll(".chip-sm").forEach(c => {
    c.classList.toggle("active", c.textContent.includes(`${cents} Cents`));
  });
}

function updateExtentSqmDisplay(cents) {
  const sqmEl = document.getElementById("extent-sqm-calc");
  const cVal = parseFloat(cents) || 0;
  if (sqmEl) sqmEl.textContent = (cVal * 40.4686).toFixed(1);
}

/* Tab 1 Action: Execute Auto-Detect from OSM / Walls */
async function executeAutoDetectBoundaries() {
  const btn = document.getElementById("btn-run-detect");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>Detecting compound walls & boundaries...</span>`;
  }

  let lat = 10.1076, lng = 76.3516;
  if (currentMarker) {
    const pos = currentMarker.getLatLng();
    lat = pos.lat;
    lng = pos.lng;
  } else if (map) {
    const c = map.getCenter();
    lat = c.lat;
    lng = c.lng;
  }

  const radius = parseInt(document.getElementById("detect-radius-select")?.value || "80");
  const targetCents = parseFloat(document.getElementById("detect-target-cents")?.value || "0") || null;

  try {
    let url = `/api/detect_boundaries?lat=${lat}&lng=${lng}&radius_m=${radius}`;
    if (targetCents) url += `&cents=${targetCents}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("Boundary detection request failed");
    const data = await res.json();

    if (data.polygon_coordinates && data.polygon_coordinates.length >= 3) {
      applyPlotPolygon(data.polygon_coordinates, {
        title: data.source_title,
        extentCents: data.extent_cents,
        surveyNo: data.survey_no,
        village: data.village,
        source: data.source === 'osm_boundary' ? 'Physical Wall / Fence Boundary' : 'Square outline from the extent'
      });
      closeAutoDemarcateModal();

      let fmbInfo = "";
      if (data.fmb_dimensions_m && data.fmb_dimensions_m.length) {
        fmbInfo = `<br><strong>FMB Boundary Dimensions:</strong><ul style="margin:4px 0 0 16px;">` +
          data.fmb_dimensions_m.map(f => `<li>${f.edge}: ${f.length_m}m (${f.type})</li>`).join("") +
          `</ul>`;
      }

      appendMsg("agent", `
        <div style="background:#eef5f5; border:1px solid #a8cfd1; border-radius:10px; padding:12px; margin:6px 0;">
          <div style="font-weight:700; color:#0d7680; font-size: var(--fs-14); display:flex; align-items:center; gap:6px;">
            <span>◆</span> <span>${data.source_title} Demarcated</span>
          </div>
          <div style="font-size: var(--fs-14); color:#0a5c63; margin-top:6px;">
            Extent: <strong>${data.extent_cents} Cents</strong> (${(data.extent_cents * 40.4686).toFixed(1)} m²) | Perimeter: <strong>${data.perimeter_m}m</strong><br>
            Source: <em>${data.source}</em>
            ${fmbInfo}
          </div>
          <div style="margin-top:8px; font-size: var(--fs-12); color:#0d7680; background:#dcebec; padding:6px 10px; border-radius:6px;">
            ${data.message}
          </div>
        </div>
      `);
    } else {
      alert("No closed boundary detected within search radius. Try increasing search radius or use Deed Extent Generator.");
    }
  } catch (err) {
    alert("Boundary detection error: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Detect Surrounding Boundaries</span>`;
    }
  }
}

/* Tab 2 Action: Generate from Deed Extent (Cents) */
function executeGenerateExtentPlot() {
  const cents = parseFloat(document.getElementById("custom-extent-input")?.value || "10.0");
  const ratio = document.getElementById("extent-aspect-ratio")?.value || "1:1";

  let lat = 10.1076, lng = 76.3516;
  if (currentMarker) {
    const pos = currentMarker.getLatLng();
    lat = pos.lat;
    lng = pos.lng;
  } else if (map) {
    const c = map.getCenter();
    lat = c.lat;
    lng = c.lng;
  }

  const coords = generateCalibratedFootprint(lat, lng, cents, ratio);
  applyPlotPolygon(coords, {
    title: `${cents} Cents Calibrated Footprint`,
    extentCents: cents,
    surveyNo: "Custom Deed Extent",
    village: "Inspected Plot",
    roadWidth: 3.2,
    source: `Calibrated Extent Footprint (${ratio})`
  });
  closeAutoDemarcateModal();

  appendMsg("agent", `
    <div style="background:#eef5f5; border:1px solid #a8cfd1; border-radius:10px; padding:12px; margin:6px 0;">
      <div style="font-weight:700; color:#0d7680; font-size: var(--fs-14);">
        Calibrated Extent Demarcated: ${cents} Cents
      </div>
      <div style="font-size: var(--fs-14); color:#0a5c63; margin-top:4px;">
        Placed exact ${cents} Cents (${(cents * 40.4686).toFixed(1)} m²) plot footprint with aspect ratio <strong>${ratio}</strong>.<br>
        Each corner stone${currentLanguage === 'ml' ? ' (<em>സർവേ കല്ല്</em>)' : ''} can now be dragged on the satellite map to align with physical fences or trees.
      </div>
    </div>
  `);
}

/* Tab 3 Action: BhuNaksha FMB Lookup */
async function executeFetchCadastralParcel() {
  const meta = (window._lastDeedData && window._lastDeedData.metadata) || {};
  const surveyNo = document.getElementById("cadastral-survey-input")?.value.trim() || meta.re_survey_no || meta.survey_no;
  const village = document.getElementById("cadastral-village-input")?.value.trim() || meta.village;
  if (!surveyNo || !village) {
    alert(currentLanguage === "ml" ? "സർവേ നമ്പറും വില്ലേജും നൽകുക." : "Enter the survey number and village.");
    return;
  }
  const cents = parseFloat(document.getElementById("cadastral-cents-input")?.value || "10.0");

  let lat = 10.1076, lng = 76.3516;
  if (currentMarker) {
    const pos = currentMarker.getLatLng();
    lat = pos.lat;
    lng = pos.lng;
  } else if (map) {
    const c = map.getCenter();
    lat = c.lat;
    lng = c.lng;
  }

  try {
    const res = await fetch(`/api/cadastral_sketch?survey_no=${encodeURIComponent(surveyNo)}&village=${encodeURIComponent(village)}&cents=${cents}&lat=${lat}&lng=${lng}`);
    if (!res.ok) throw new Error("Failed to fetch cadastral parcel");
    const data = await res.json();

    if (data.polygon_coordinates) {
      applyPlotPolygon(data.polygon_coordinates, {
        title: `Re-Sy ${data.survey_no} (approximate outline)`,
        extentCents: data.extent_cents,
        surveyNo: data.survey_no,
        village: data.village,
        source: "Square outline from the extent"
      });
      closeAutoDemarcateModal();

      let fmbListHtml = "";
      if (data.fmb_dimensions_m) {
        fmbListHtml = data.fmb_dimensions_m.map(f => `<li><strong>${f.edge}:</strong> ${f.length_m}m <em>(${f.type})</em></li>`).join("");
      }

      appendMsg("agent", `
        <div style="background:#fbf0e0; border:1px solid #ecd2a8; border-radius:10px; padding:12px; margin:6px 0;">
          <div style="display:flex; align-items:center; gap:8px; font-weight:700; color:#8a4d00; font-size: var(--fs-16);">
            <span>§</span> <span>Approximate outline: Survey ${data.survey_no}, ${data.village}</span>
          </div>
          <div style="font-size: var(--fs-14); color:#4a2a00; margin-top:6px;">
            A square of <strong>${data.extent_cents} cents</strong> at the pin. The real shape is in the FMB sketch from the Village Office or <a href="https://bhunaksha.kerala.gov.in" target="_blank" rel="noopener noreferrer">BhuNaksha</a>.
          </div>
          <div style="font-size: var(--fs-14); margin-top:8px;">
            <strong>Sides of the square (meters):</strong>
            <ul style="margin-left:18px; margin-top:4px;">${fmbListHtml}</ul>
          </div>
        </div>
      `);
    }
  } catch (err) {
    alert("Error fetching cadastral sketch: " + err.message);
  }
}

/* Tab 4 Action: Import Coordinates / Survey Files */
function executeImportCoordinates() {
  const text = document.getElementById("import-coords-text")?.value.trim();
  if (!text) {
    alert("Please paste survey coordinates (one lat,lng per line)");
    return;
  }

  const lines = text.split("\n");
  const coords = [];
  for (let line of lines) {
    line = line.trim();
    if (!line) continue;
    const parts = line.split(/[,\s\t]+/);
    if (parts.length >= 2) {
      const lat = parseFloat(parts[0]);
      const lng = parseFloat(parts[1]);
      if (!isNaN(lat) && !isNaN(lng)) {
        coords.push([lat, lng]);
      }
    }
  }

  if (coords.length < 3) {
    alert("Please provide at least 3 valid coordinate points to form a polygon.");
    return;
  }

  applyPlotPolygon(coords, {
    title: "Imported Survey Boundary",
    surveyNo: "Survey Import",
    village: "Field Measurement",
    source: "Imported Total Station / GPS Waypoints"
  });
  closeAutoDemarcateModal();
}

function handleSurveyFileUpload(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    const content = e.target.result;
    const coords = [];

    try {
      const geo = JSON.parse(content);
      if (geo.type === "FeatureCollection" && geo.features && geo.features[0]) {
        const geom = geo.features[0].geometry;
        if (geom.type === "Polygon" && geom.coordinates && geom.coordinates[0]) {
          geom.coordinates[0].forEach(pt => coords.push([pt[1], pt[0]]));
        }
      }
    } catch (_) {
      const regex = /<coordinates>([\s\S]*?)<\/coordinates>/i;
      const match = content.match(regex);
      if (match) {
        const rawCoords = match[1].trim().split(/\s+/);
        rawCoords.forEach(c => {
          const p = c.split(',');
          if (p.length >= 2) {
            const lng = parseFloat(p[0]);
            const lat = parseFloat(p[1]);
            if (!isNaN(lat) && !isNaN(lng)) coords.push([lat, lng]);
          }
        });
      } else {
        const lines = content.split("\n");
        lines.forEach(l => {
          const p = l.trim().split(/[,\s\t]+/);
          if (p.length >= 2) {
            const lat = parseFloat(p[0]);
            const lng = parseFloat(p[1]);
            if (!isNaN(lat) && !isNaN(lng)) coords.push([lat, lng]);
          }
        });
      }
    }

    if (coords.length >= 3) {
      applyPlotPolygon(coords, {
        title: file.name,
        surveyNo: "Survey File",
        village: "Imported",
        source: `Imported from ${file.name}`
      });
      closeAutoDemarcateModal();
    } else {
      alert("Could not extract at least 3 polygon boundary coordinates from this file.");
    }
  };
  reader.readAsText(file);
}

function searchLocation() {
  const query = document.getElementById("map-search").value.trim();
  if (!query) return;

  const coordsMatch = query.match(/^([-+]?[0-9]*\.?[0-9]+)\s*,\s*([-+]?[0-9]*\.?[0-9]+)$/);
  if (coordsMatch) {
    const lat = parseFloat(coordsMatch[1]);
    const lng = parseFloat(coordsMatch[2]);
    map.setView([lat, lng], 17);
    setPin(lat, lng);
    return;
  }

  const qLower = query.toLowerCase();
  for (const [key, p] of Object.entries(KERALA_PRESETS)) {
    if (key.toLowerCase().includes(qLower) || p.name.toLowerCase().includes(qLower) || (p.village && p.village.toLowerCase().includes(qLower))) {
      applyLocationPreset(key);
      return;
    }
  }

  const keralaQuery = query.toLowerCase().includes("kerala") ? query : `${query}, Kerala, India`;
  fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(keralaQuery)}`)
    .then(res => res.json())
    .then(data => {
      if (data && data.length > 0) {
        const item = data[0];
        const lat = parseFloat(item.lat);
        const lng = parseFloat(item.lon);
        map.setView([lat, lng], 17);
        setPin(lat, lng);
        updateHUDLocation(lat, lng, item.display_name.split(',')[0]);
      } else {
        alert("Location not found. Please try entering village name with district (e.g. 'Aluva, Ernakulam') or GPS coordinates.");
      }
    })
    .catch(err => {
      console.error("Geocoding failed:", err);
    });
}

let currentElevationData = null;

async function fetchElevationAndFlood(lat, lng, localityName, centsVal) {
  const elevValEl = document.getElementById("hud-elevation-text");
  const badgeEl = document.getElementById("hud-flood-badge");
  const basinEl = document.getElementById("hud-basin-text");

  const isMl = currentLanguage === "ml";
  const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;

  if (elevValEl) elevValEl.textContent = isMl ? "കണക്കാക്കുന്നു..." : "Calculating...";
  if (badgeEl) {
    badgeEl.className = "badge-road warn";
    badgeEl.textContent = isMl ? "പരിശോധിക്കുന്നു..." : "Assessing Flood...";
  }

  try {
    const res = await fetch("/api/plot_elevation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lat: lat,
        lng: lng,
        locality: localityName || undefined,
        cents: centsVal || undefined
      })
    });
    if (!res.ok) throw new Error("Elevation request failed");
    const data = await res.json();
    currentElevationData = data;
    window.currentElevationData = data;

    if (elevValEl) {
      const isEstimate = data.resolution_meters == null;
      elevValEl.textContent = `${isEstimate ? "≈" : ""}${data.elevation_meters} ${t.hudMslUnit}${isEstimate ? (isMl ? " (ഏകദേശം)" : " (rough estimate)") : ""}`;
    }
    if (basinEl) {
      const basinName = getLocalizedBasinName(data.river_basin, isMl);
      basinEl.textContent = `${basinName} • ${t.hudBasinPlinth} ≥${data.recommended_plinth_height_m}m`;
    }
    if (badgeEl) {
      if (data.flood_risk_level === "LOW") {
        badgeEl.className = "badge-road pass";
        badgeEl.textContent = t.hudElevationRiskLow;
      } else if (data.flood_risk_level === "MODERATE") {
        badgeEl.className = "badge-road warn";
        badgeEl.textContent = t.hudElevationRiskMod;
      } else if (data.flood_risk_level === "HIGH") {
        badgeEl.className = "badge-road fail";
        badgeEl.textContent = t.hudElevationRiskHigh;
      } else {
        badgeEl.className = "badge-road fail";
        badgeEl.textContent = t.hudElevationRiskCrit;
      }
      badgeEl.title = data.ksdma_hazard_advisory;
    }
  } catch (err) {
    console.warn("Failed to fetch plot elevation:", err);
    if (elevValEl) elevValEl.textContent = isMl ? "ലഭ്യമല്ല" : "Elevation N/A";
    if (badgeEl) {
      badgeEl.className = "badge-road warn";
      badgeEl.textContent = isMl ? "▲ നേരിട്ട് പരിശോധിക്കുക" : "▲ Check On Ground";
    }
  }
}

function updateHUDLocation(lat, lng, localityName, centsVal, roadVal) {
  document.getElementById("map-hud").style.display = "";
  document.getElementById("map-toolbar")?.classList.remove("needs-pin");
  updateGuidanceBarText();
  markStepDone(3);
  document.getElementById("hud-coords").textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  
  const isMl = currentLanguage === "ml";
  const t = TRANSLATIONS[currentLanguage] || TRANSLATIONS.en;

  if (localityName) {
    document.getElementById("hud-locality-title").textContent = `${localityName}`;
  } else {
    document.getElementById("hud-locality-title").textContent = isMl
      ? `അക്ഷാംശം ${lat.toFixed(4)}, രേഖാംശം ${lng.toFixed(4)}`
      : `Lat ${lat.toFixed(4)}, Lng ${lng.toFixed(4)}`;
  }

  if (centsVal) {
    document.getElementById("hud-cents").textContent = `${centsVal.toFixed(2)} ${t.hudCentsUnit}`;
    const sqm = centsVal * 40.4686;
    const ares = sqm / 100;
    document.getElementById("hud-sqm").textContent = `${ares.toFixed(2)} ${t.hudAresUnit} (${sqm.toFixed(1)} ${t.hudSqMUnit})`;
  }

  if (roadVal) {
    document.getElementById("hud-road-text").textContent = `${roadVal.toFixed(1)} ${t.hudMetersUnit}`;
    const badgeEl = document.getElementById("hud-road-badge");
    if (roadVal >= 3.0) {
      badgeEl.className = "badge-road pass";
      badgeEl.textContent = t.hudRoadPass;
    } else if (roadVal >= 1.2) {
      badgeEl.className = "badge-road warn";
      badgeEl.textContent = t.hudRoadWarn;
    } else {
      badgeEl.className = "badge-road fail";
      badgeEl.textContent = t.hudRoadFail;
    }
  }

  const gmapsLink = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
  const elGmapsBtn = document.getElementById("btn-hud-maps") || document.getElementById("btn-open-gmaps");
  if (elGmapsBtn) elGmapsBtn.setAttribute("href", gmapsLink);

  fetchElevationAndFlood(lat, lng, localityName, centsVal);
}

function toggleHUD() {
  const hud = document.getElementById("map-hud");
  const btn = document.getElementById("hud-toggle-btn");
  const isMin = hud.classList.toggle("minimized");
  btn.textContent = isMin ? "▴" : "▾";
  btn.title = isMin ? "Expand" : "Collapse";
  updateHudSummary();
}

// One-line summary shown while the HUD is collapsed: extent · road · elevation.
// Boxes without a measured or fetched value stay hidden.
function updateHudSummary() {
  const el = document.getElementById("hud-summary");
  if (!el) return;
  const txt = id => (document.getElementById(id)?.textContent || "").trim();
  const has = id => {
    const v = txt(id);
    return !!v && v !== "—" && !/not measured|^0\.00/i.test(v);
  };
  const showBox = (id, show) => {
    const box = document.getElementById(id)?.closest(".hud-stat-box");
    if (box) box.style.display = show ? "" : "none";
  };
  showBox("hud-coords", false);
  showBox("hud-cents", has("hud-cents"));
  showBox("hud-sqm", has("hud-cents"));
  showBox("hud-road-text", has("hud-road-text"));
  showBox("hud-elevation-text", has("hud-elevation-text"));
  el.textContent = ["hud-cents", "hud-road-text", "hud-elevation-text"].filter(has).map(txt).join(" · ");
}

function initHud() {
  const grid = document.querySelector("#map-hud .hud-stats-grid");
  if (grid) new MutationObserver(updateHudSummary).observe(grid, { subtree: true, childList: true, characterData: true });
  updateHudSummary();
  toggleHUD();
}

function toggleChecklist(forceState) {
  const panel = document.getElementById("checklist-panel");
  if (forceState !== undefined) {
    panel.classList.toggle("visible", forceState);
  } else {
    panel.classList.toggle("visible");
  }
}

function updateChecklistProgress() {
  const checks = [
    document.getElementById("chk-kallu")?.checked,
    document.getElementById("chk-road")?.checked,
    document.getElementById("chk-wetland")?.checked,
    document.getElementById("chk-ht")?.checked,
    document.getElementById("chk-flood")?.checked
  ];
  const count = checks.filter(Boolean).length;
  document.getElementById("chk-badge").textContent = `${count}/5`;
  if (count === 5) {
    document.getElementById("chk-badge").style.background = "#0d7680";
  } else {
    document.getElementById("chk-badge").style.background = "#990f3d";
  }
}

function calculatePolygonArea(latlngs) {
  if (latlngs.length < 3) return 0;
  const radius = 6378137;
  let total = 0;
  for (let i = 0; i < latlngs.length; i++) {
    const p1 = latlngs[i];
    const p2 = latlngs[(i + 1) % latlngs.length];
    const x1 = (p1.lng * Math.PI) / 180;
    const y1 = (p1.lat * Math.PI) / 180;
    const x2 = (p2.lng * Math.PI) / 180;
    const y2 = (p2.lat * Math.PI) / 180;
    total += (x2 - x1) * (2 + Math.sin(y1) + Math.sin(y2));
  }
  return Math.abs((total * radius * radius) / 2);
}

function calculateDistance(p1, p2) {
  const R = 6371000;
  const dLat = (p2.lat - p1.lat) * Math.PI / 180;
  const dLng = (p2.lng - p1.lng) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(p1.lat * Math.PI / 180) * Math.cos(p2.lat * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

const sendToAuditor = (...args) => sendPlotToAuditor(...args);
function sendPlotToAuditor() {
  const coords = document.getElementById("hud-coords").textContent;
  const locality = document.getElementById("hud-locality-title").textContent;
  const cents = document.getElementById("hud-cents").textContent;
  const roadM = document.getElementById("hud-road-text").textContent;
  const roadBadge = document.getElementById("hud-road-badge").textContent;

  let elevInfo = "";
  if (window.currentElevationData) {
    const elev = window.currentElevationData;
    elevInfo = `Plot Elevation: ${elev.elevation_meters}m MSL (Flood Risk: ${elev.flood_risk_level}, Basin: ${elev.river_basin || 'Local Watershed'}, Recommended Plinth: ≥${elev.recommended_plinth_height_m}m). `;
  } else {
    const elevText = document.getElementById("hud-elevation-text")?.textContent;
    const floodBadge = document.getElementById("hud-flood-badge")?.textContent;
    if (elevText) {
      elevInfo = `Plot Elevation: ${elevText} (${floodBadge}). `;
    }
  }

  const isMl = currentLanguage === "ml";
  let promptText = "";
  if (isMl) {
    promptText = `${locality} പ്രദേശത്തുള്ള വസ്തു പരിശോധിക്കുകയാണ് (ജിപിഎസ് അക്ഷാംശ രേഖാംശങ്ങൾ: ${coords}). ` +
      `ഉപഗ്രഹ മാപ്പിൽ നിന്ന് ലഭിച്ച ഏകദേശ വിസ്തീർണ്ണം: ${cents}. ` +
      `വഴിയുടെ വീതി: ${roadM} (${roadBadge}). ` +
      elevInfo +
      `ഇതിനെ കേരള പഞ്ചായത്ത് കെട്ടിട നിർമ്മാണ ചട്ടങ്ങൾ (KPBR 2019) പ്രകാരമുള്ള വഴി വീതി, സെറ്റ്ബാക്ക്, ` +
      `പ്രളയസാധ്യത (KSDMA & 2018 വെള്ളപ്പൊക്ക മേഖല) എന്നിവയുമായി ഒത്തുനോക്കി, ഈ സ്ഥലത്ത് നേരിട്ട് പരിശോധിക്കേണ്ട കാര്യങ്ങൾ (സർവേ കല്ല്, നിലം തരംമാറ്റൽ) പട്ടികപ്പെടുത്തുക.`;
  } else {
    promptText = `Auditing property in ${locality} (GPS Coordinates: ${coords}). ` +
      `Demarcated Extent from Satellite Map: ${cents}. ` +
      `Access Road Width: ${roadM} (${roadBadge}). ` +
      elevInfo +
      `Please cross-verify against Kerala Panchayat Building Rules (KPBR 2019) access road width and setback requirements, ` +
      `flood exposure (KSDMA & 2018 flood zone), and list the on-site checks for this plot (survey stones / FMB boundaries, paddy land / wetland status).`;
  }

  if (currentViewMode === "map") {
    setViewMode("split");
  }

  sendPrompt(promptText);
}

// Survey no, village and extent of the user's plot: from the scanned deed, else asked.
function askPlotIdentity() {
  const meta = (window._lastDeedData && window._lastDeedData.metadata) || {};
  const isMl = currentLanguage === 'ml';
  const surveyNo = meta.re_survey_no || meta.survey_no || prompt(isMl ? "സർവേ / റീ-സർവേ നമ്പർ (ഉദാ. 182/4):" : "Survey / re-survey number (e.g. 182/4):");
  if (!surveyNo) return null;
  const village = meta.village || prompt(isMl ? "വില്ലേജ്:" : "Village:");
  if (!village) return null;
  const cents = parseFloat(meta.extent_cents) || parseFloat(prompt(isMl ? "വിസ്തീർണ്ണം (സെന്റ്):" : "Extent (cents):") || "");
  if (!cents) return null;
  return { surveyNo: String(surveyNo).trim(), village: String(village).trim(), cents };
}

/* BhuNaksha Cadastral Survey Overlay */
let _cadastralLayer = null;

async function fetchCadastralOverlay() {
  const center = currentMarker ? currentMarker.getLatLng() : (map ? map.getCenter() : { lat: 10.1076, lng: 76.3516 });
  
  const plot = askPlotIdentity();
  if (!plot) return;
  const { surveyNo, village, cents } = plot;

  try {
    const res = await fetch(`/api/cadastral_sketch?survey_no=${encodeURIComponent(surveyNo)}&village=${encodeURIComponent(village)}&cents=${cents}&lat=${center.lat}&lng=${center.lng}`);
    if (!res.ok) throw new Error("Could not fetch cadastral parcel");
    const data = await res.json();

    if (_cadastralLayer && map) {
      map.removeLayer(_cadastralLayer);
    }

    if (map && data.polygon_coordinates) {
      _cadastralLayer = L.polygon(data.polygon_coordinates, {
        color: '#a35c00',
        weight: 3,
        dashArray: '6, 6',
        fillColor: '#fbf0e0',
        fillOpacity: 0.35
      }).addTo(map);

      let tooltipContent = `<b>Approximate outline (not the FMB)</b><br>Survey No: <b>${data.survey_no}</b> (${data.village})<br>Extent: <b>${data.extent_cents} Cents</b><br><hr style="margin:4px 0;">`;
      if (data.fmb_dimensions_m && data.fmb_dimensions_m.length) {
        tooltipContent += `<b>Sides (meters, approximate):</b><br>`;
        data.fmb_dimensions_m.forEach(f => {
          tooltipContent += `• ${f.edge}: ${f.length_m}m (${f.type})<br>`;
        });
      }
      _cadastralLayer.bindPopup(tooltipContent).openPopup();
      map.fitBounds(_cadastralLayer.getBounds(), { padding: [40, 40] });

      // Demarcate as active plot polygon with corner stones
      applyPlotPolygon(data.polygon_coordinates, {
        title: `Re-Sy ${data.survey_no} (approximate outline)`,
        extentCents: data.extent_cents,
        surveyNo: data.survey_no,
        village: data.village,
        source: "Square outline from the extent"
      });
    }

    let fmbListHtml = "";
    if (data.fmb_dimensions_m) {
      fmbListHtml = data.fmb_dimensions_m.map(f => `<li><strong>${f.edge}:</strong> ${f.length_m}m <em>(${f.type})</em></li>`).join("");
    }

    appendMsg("agent", `
      <div style="background:#fbf0e0; border:1px solid #ecd2a8; border-radius:10px; padding:12px; margin:6px 0;">
        <div style="display:flex; align-items:center; gap:8px; font-weight:700; color:#8a4d00; font-size: var(--fs-16);">
          <span>§</span> <span>Approximate outline: Survey ${data.survey_no}, ${data.village}</span>
        </div>
        <div style="font-size: var(--fs-14); color:#4a2a00; margin-top:6px;">
          A square of <strong>${data.extent_cents} cents</strong> at the pin. The real shape is in the FMB sketch from the Village Office or <a href="https://bhunaksha.kerala.gov.in" target="_blank" rel="noopener noreferrer">BhuNaksha</a>.
        </div>
        <div style="font-size: var(--fs-14); margin-top:8px;">
          <strong>Sides of the square (meters):</strong>
          <ul style="margin-left:18px; margin-top:4px;">${fmbListHtml}</ul>
        </div>
        <div style="margin-top:8px; font-size: var(--fs-12); color:#6b3d00; background:#fbf0e0; padding:6px 10px; border-radius:6px;">
          ▲ <strong>Field Instruction:</strong> Cross-verify all 4 boundary stones${currentLanguage === 'ml' ? ' (<em>സർവേ കല്ലുകൾ</em>)' : ''} against the above meter dimensions. Never purchase based solely on seller's oral demarcations.
        </div>
      </div>
    `);

  } catch (err) {
    appendMsg("agent", `<span style="color:#990f3d;">▲ Error retrieving BhuNaksha sketch: ${err.message}</span>`);
  }
}

/* Agricultural Data Bank Status Verification */
async function checkDataBankStatus() {
  const center = currentMarker ? currentMarker.getLatLng() : (map ? map.getCenter() : { lat: 10.1076, lng: 76.3516 });
  
  const plot = askPlotIdentity();
  if (!plot) return;
  const { surveyNo, village, cents } = plot;

  try {
    const res = await fetch(`/api/databank_check?survey_no=${encodeURIComponent(surveyNo)}&village=${encodeURIComponent(village)}&cents=${cents}&fair_value=240000&lang=${currentLanguage}`);
    if (!res.ok) throw new Error("Could not verify Data Bank status");
    const data = await res.json();

    window._lastDatabankData = data;
    const isListed = data.is_listed_in_databank;
    const badgeColor = isListed === true ? "#990f3d" : (isListed === false ? "#0d7680" : "#a35c00");
    const badgeText = isListed === true ? "■ LISTED IN DATA BANK (Nilam)" : (isListed === false ? "● NOT IN DATA BANK" : "▲ NO RECORD ON FILE");

    let feeHtml = "";
    if (data.fee_calculation) {
      const f = data.fee_calculation;
      feeHtml = `
        <div style="background:#f6ede2; border:1px solid #e9decf; border-radius:6px; padding:8px; margin-top:8px; font-size: var(--fs-12);">
          <strong>Section 27A Conversion Fee:</strong> ${f.is_fee_exempt ? '<span style="color:#0d7680; font-weight:700;">₹0 (Free exemption under 25 cents)</span>' : `₹${f.statutory_conversion_fee_inr.toLocaleString()} (${f.applicable_fee_percentage}%)`}
          <br><small style="color:#66605c;">${f.statutory_citation} • Fair Value: ₹${f.fair_value_per_are_inr.toLocaleString()}/Are</small>
        </div>
      `;
    }

    appendMsg("agent", `
      <div style="background:#ffffff; border:1px solid #e9decf; border-radius:10px; padding:12px; margin:6px 0; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <strong style="color:#990f3d; font-size: var(--fs-14);">Kerala Agricultural Data Bank Audit (2008 Act)</strong>
          <span style="font-size: var(--fs-12); font-weight:700; color:#fff; background:${badgeColor}; padding:2px 8px; border-radius:12px;">${badgeText}</span>
        </div>
        <div style="font-size: var(--fs-14); color:#4d4845;">
          Survey: <strong>${data.survey_no}</strong> | Krishi Bhavan: <strong>${data.krishi_bhavan_name}</strong><br>
          Classification: <strong>${data.entry_status}</strong><br>
          Required Statutory Form: <strong>${data.recommended_statutory_form}</strong>
        </div>
        ${feeHtml}
        <div style="margin-top:8px; font-size: var(--fs-12); color:#a35c00; background:#fbf0e0; padding:6px 8px; border-radius:6px;">
          <strong>Building Permit Status:</strong> ${data.building_permit_eligibility}
        </div>
        ${isListed == null ? `<div style="margin-top:6px; font-size: var(--fs-12);">${data.risk_advisory}</div>` : ''}
        <div class="deed-action-buttons">
          <button class="deed-action-btn primary" onclick="onStepClick(4)">${currentLanguage === 'ml' ? "ഉടമയോട് ചോദിക്കുക" : "Ask seller"}</button>
        </div>
      </div>
    `);

  } catch (err) {
    appendMsg("agent", `<span style="color:#990f3d;">▲ Error checking Data Bank: ${err.message}</span>`);
  }
}
