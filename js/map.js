/* ============================================
   Sailing Oroboro — Journey Map
   ============================================ */

const WAYPOINTS = [
  { name: "Cape Town, South Africa",     coords: [-33.925,  18.424], date: "Sep 2018",  slug: "cape-town-33-54-219-s-18-25-157-e",     region: "south-africa" },
  { name: "Lüderitz, Namibia",           coords: [-26.648,  15.156], date: "Dec 2018",  slug: "kolmanskop-namibia",                     region: "namibia" },
  { name: "Walvis Bay, Namibia",         coords: [-22.957,  14.505], date: "Dec 2018",  slug: "hottentot-bay-namibia",                  region: "namibia" },
  { name: "Tropic of Capricorn",         coords: [-23.5,    -6.0],   date: "Jan 2019",  slug: "the-tropic-of-capricorn",                region: "atlantic" },
  { name: "South Atlantic Ocean",        coords: [-20.0,   -15.0],   date: "Feb 2019",  slug: "crossing-the-south-atlantic-ocean",      region: "atlantic" },
  { name: "St Helena",                   coords: [-15.965,  -5.709], date: "Mar 2019",  slug: "st-helena",                              region: "atlantic" },
  { name: "Trindade, Brazil",            coords: [-20.514, -29.328], date: "Mar 2019",  slug: "trindade",                               region: "brazil" },
  { name: "Vitória, Brazil",            coords: [-20.316, -40.313], date: "Mar 2019",  slug: "welcome-to-brazil",                      region: "brazil" },
  { name: "Ilha Grande",                 coords: [-23.168, -44.206], date: "Apr 2019",  slug: "ilha-grande",                            region: "brazil" },
  { name: "Rio de Janeiro",              coords: [-22.907, -43.173], date: "Apr 2019",  slug: "carnival-in-rio-de-janeiro",             region: "brazil" },
  { name: "Cabo Frio",                   coords: [-22.889, -42.018], date: "May 2019",  slug: "cabo-frio",                              region: "brazil" },
  { name: "Búzios",                     coords: [-22.747, -41.883], date: "May 2019",  slug: "armacao-dos-buzios-simply-known-as-buzios", region: "brazil" },
  { name: "Guarapari",                   coords: [-20.670, -40.501], date: "May 2019",  slug: "guarapari",                              region: "brazil" },
  { name: "Abrolhos",                    coords: [-17.968, -38.702], date: "May 2019",  slug: "abrolhos",                               region: "brazil" },
  { name: "Cumuruxatiba",                coords: [-17.088, -39.183], date: "May 2019",  slug: "cumuruxatiba",                           region: "brazil" },
  { name: "Porto Seguro",                coords: [-16.450, -39.061], date: "May 2019",  slug: "porto-seguro",                           region: "brazil" },
  { name: "Santa Cruz Cabrália",        coords: [-16.276, -39.022], date: "May 2019",  slug: "terra-a-vista-santa-cruz-cabralia",      region: "brazil" },
  { name: "Ilhéus",                     coords: [-14.789, -39.046], date: "2019",      slug: "ilheus",                                 region: "brazil" },
  { name: "Itacaré",                    coords: [-14.275, -38.999], date: "2019",      slug: "itacare",                                region: "brazil" },
  { name: "Camamù Bay",                 coords: [-13.945, -39.099], date: "2019",      slug: "camamu-bay",                             region: "brazil" },
  { name: "Salvador de Bahia",           coords: [-12.971, -38.501], date: "2019",      slug: "salvador-de-bahia",                      region: "brazil" },
  { name: "Morro de São Paulo",         coords: [-13.382, -38.909], date: "2019",      slug: "morro-de-sao-paulo",                     region: "brazil" },
  { name: "Itaparica",                   coords: [-12.891, -38.685], date: "2019",      slug: "itaparica",                              region: "brazil" },
  { name: "Recife",                      coords: [ -8.048, -34.877], date: "2019",      slug: "recife",                                 region: "brazil" },
  { name: "Olinda",                      coords: [ -7.999, -34.846], date: "2019",      slug: "olinda",                                 region: "brazil" },
  { name: "Jacaré",                     coords: [ -7.030, -34.849], date: "2019",      slug: "jacare",                                 region: "brazil" },
  { name: "Pipa Beach",                  coords: [ -6.228, -35.047], date: "2019",      slug: "pipa-beach",                             region: "brazil" },
  { name: "João Pessoa",               coords: [ -7.115, -34.863], date: "2019",      slug: "joao-pessoa",                            region: "brazil" },
  { name: "Fortaleza",                   coords: [ -3.717, -38.543], date: "2019",      slug: "fortaleza",                              region: "brazil" },
  { name: "French Guiana",               coords: [  4.937, -52.326], date: "2019",      slug: "french-guiana",                          region: "caribbean" },
  { name: "Trinidad",                    coords: [ 10.692, -61.222], date: "2019",      slug: "trinidad",                               region: "caribbean" },
  { name: "Tobago",                      coords: [ 11.188, -60.686], date: "2019",      slug: "tobago",                                 region: "caribbean" },
  { name: "Grenada (COVID Lockdown)",    coords: [ 12.117, -61.679], date: "2019–2021", slug: "covid-19-in-paradise",                   region: "caribbean" },
  { name: "US Virgin Islands",           coords: [ 18.338, -64.894], date: "2021",      slug: "us-virgin-islands",                      region: "caribbean" },
  { name: "Spanish Virgin Islands",      coords: [ 18.350, -65.450], date: "2021",      slug: "spanish-virgin-islands",                 region: "caribbean" },
  { name: "Puerto Rico",                 coords: [ 18.221, -66.590], date: "2021",      slug: "puerto-rico",                            region: "caribbean" },
  { name: "Dominican Republic",          coords: [ 18.486, -69.931], date: "2021",      slug: "dominican-republic",                     region: "caribbean" },
  { name: "Bahamas",                     coords: [ 24.698, -77.794], date: "2021",      slug: "sailing-in-the-bahamas",                 region: "caribbean" },
  { name: "2nd Atlantic Crossing",       coords: [ 38.0,   -30.0],   date: "2021",      slug: "2nd-atlantic-crossing",                  region: "atlantic2" },
  { name: "Azores",                      coords: [ 38.525, -28.714], date: "2021",      slug: null,                                     region: "atlantic2" },
  { name: "Lisbon, Portugal",            coords: [ 38.717,  -9.140], date: "2021",      slug: null,                                     region: "europe" },
  { name: "Gibraltar",                   coords: [ 36.141,  -5.354], date: "2021",      slug: null,                                     region: "europe" },
  { name: "Mediterranean",               coords: [ 38.0,    15.0],   date: "2022+",     slug: null,                                     region: "europe" },
  { name: "Greece (current)",            coords: [ 37.9,    23.7],   date: "2024+",     slug: null,                                     region: "europe" },
];

// Route line (all coords in order)
const ROUTE_COORDS = WAYPOINTS.map(w => w.coords);

function initMap(containerId) {
  const map = L.map(containerId, {
    center: [10, -20],
    zoom: 3,
    zoomControl: true,
  });

  // Tile layer — CartoDB Positron (clean, light)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 18,
  }).addTo(map);

  // Route polyline
  L.polyline(ROUTE_COORDS, {
    color: '#2E86AB',
    weight: 2.5,
    opacity: 0.7,
    dashArray: '6, 4',
    lineJoin: 'round',
  }).addTo(map);

  // Custom icon
  const makeIcon = (color = '#2E86AB') => L.divIcon({
    className: '',
    html: `<div style="
      width:12px;height:12px;
      background:${color};
      border:2.5px solid white;
      border-radius:50%;
      box-shadow:0 2px 6px rgba(0,0,0,0.35);
    "></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });

  // Current location icon
  const currentIcon = L.divIcon({
    className: '',
    html: `<div style="
      width:16px;height:16px;
      background:#E76F51;
      border:3px solid white;
      border-radius:50%;
      box-shadow:0 2px 8px rgba(231,111,81,0.6);
      animation:pulse 2s infinite;
    "></div>
    <style>@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(231,111,81,0.4)}50%{box-shadow:0 0 0 8px rgba(231,111,81,0)}}</style>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });

  WAYPOINTS.forEach((wp, i) => {
    const isLast = i === WAYPOINTS.length - 1;
    const icon = isLast ? currentIcon : makeIcon();

    const popup = wp.slug
      ? `<div style="font-family:Inter,sans-serif;min-width:160px">
           <strong style="display:block;margin-bottom:4px;color:#0B1426">${wp.name}</strong>
           <span style="font-size:12px;color:#6B7B8D">${wp.date}</span><br>
           <a href="/posts/${wp.slug}.html" style="font-size:12px;color:#2E86AB;font-weight:600;margin-top:6px;display:inline-block">Read post →</a>
         </div>`
      : `<div style="font-family:Inter,sans-serif">
           <strong style="display:block;margin-bottom:4px;color:#0B1426">${wp.name}</strong>
           <span style="font-size:12px;color:#6B7B8D">${wp.date}</span>
         </div>`;

    const marker = L.marker(wp.coords, { icon }).addTo(map);
    marker.bindPopup(popup, { maxWidth: 220, className: 'oroboro-popup' });

    // Sidebar interaction
    const item = document.querySelector(`[data-waypoint="${i}"]`);
    if (item) {
      item.addEventListener('click', () => {
        map.setView(wp.coords, 7, { animate: true });
        marker.openPopup();
        document.querySelectorAll('.waypoint-item').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
      });
    }
  });

  // Popup styles
  const style = document.createElement('style');
  style.textContent = `
    .oroboro-popup .leaflet-popup-content-wrapper {
      border-radius: 10px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.15);
      padding: 4px;
    }
    .oroboro-popup .leaflet-popup-tip { background: #fff; }
  `;
  document.head.appendChild(style);

  return map;
}

// Mini-map for homepage
function initMiniMap(containerId) {
  const map = L.map(containerId, {
    center: [10, -20],
    zoom: 2,
    zoomControl: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    dragging: false,
    attributionControl: false,
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 10,
  }).addTo(map);

  L.polyline(ROUTE_COORDS, {
    color: '#2E86AB',
    weight: 2,
    opacity: 0.8,
    dashArray: '5, 4',
  }).addTo(map);

  // Start marker
  L.circleMarker(ROUTE_COORDS[0], { radius: 5, color: '#E9C46A', fillColor: '#E9C46A', fillOpacity: 1, weight: 2 }).addTo(map);
  // End marker
  L.circleMarker(ROUTE_COORDS[ROUTE_COORDS.length - 1], { radius: 6, color: '#E76F51', fillColor: '#E76F51', fillOpacity: 1, weight: 2 }).addTo(map);

  return map;
}

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('journey-map')) initMap('journey-map');
  if (document.getElementById('mini-map'))    initMiniMap('mini-map');
});
