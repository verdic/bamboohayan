<script>
var locations = [
  {% for location in locations %}
    {
      lat: {{ location.latitude }}, 
      lng: {{ location.longitude }}},
      accession_no: '{{ location.accession_no }}',
      species: '{{ location.bamboo_species.common_name|escapejs|safe }}',
      place: '{{ location.place }}',
      area_population: {{ location.area_population }}
  {% endfor %}
];

function initMap() {
    const mapOptions = {
        center: { lat: 18.25227, lng: 121.996 },
        zoom: 8,
    };

    const map = new google.maps.Map(document.getElementById('map'), mapOptions);

    const speciesLocations = JSON.parse('{{ species_locations_json|escapejs|safe }}');

    speciesLocations.forEach((location) => {
        const marker = new google.maps.Marker({
            position: { lat: parseFloat(location.latitude), lng: parseFloat(location.longitude) },
            map: map,
            icon: {
                url: location.marker_icon,
                scaledSize: new google.maps.Size(24, 24),
            },
        });
    
        const infoWindow = new google.maps.InfoWindow({
            content: `<strong>Accession No.:</strong> ${location.accession_no}<br>
                      <strong>Species:</strong> ${location.species}<br>
                      <strong>Place:</strong> ${location.place}<br>
                      <strong>Population in the Area:</strong> ${location.area_population}`,
            disableAutoPan: true, // Prevent auto-panning
        });
    
        marker.addListener('mouseover', () => {
            infoWindow.open(map, marker);
        });
    
        marker.addListener('mouseout', () => {
            infoWindow.close();
        });
    });
    

    // Add Fullscreen Button
    const fullscreenControl = document.createElement('button');
    fullscreenControl.textContent = 'Fullscreen';
    fullscreenControl.classList.add('custom-fullscreen-control');
    map.controls[google.maps.ControlPosition.TOP_RIGHT].push(fullscreenControl);

    fullscreenControl.addEventListener('click', () => {
        const mapDiv = document.getElementById('map');
        if (!document.fullscreenElement) {
            mapDiv.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    });
}


window.initMap = initMap;

</script>