
let map;
function initMap() {
map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 18.08324, lng: 121.72634 },
    zoom: 8,
});
}
window.initMap = initMap;

