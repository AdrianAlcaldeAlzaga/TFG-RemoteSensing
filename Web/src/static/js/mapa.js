let map = L.map('map').setView([51.50521, -0.09321], 12);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

document.getElementById('select-location').addEventListener('change', function(e) {
    let coords = e.target.value.split(',');
    map.setView(coords, 13);
});