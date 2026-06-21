import json
import os


def get_mappls_api_key():
    return os.environ.get("MAPPLS_API_KEY", "").strip()


def build_marker_script(markers):
    lines = []
    for index, marker in enumerate(markers, start=1):
        label = str(marker.get("label") or f"Stop {index}").replace("'", "")
        lines.append(
            f"new mappls.Marker({{map: map, position: {{lat: {marker['lat']}, lng: {marker['lon']}}}, "
            f"popupHtml: '{label}'}});"
        )
    return "\n".join(lines)


def build_traffic_map_html(api_key, center_lat, center_lon, zoom, markers):
    marker_script = build_marker_script(markers)
    html = f"""
<div id="mappls-traffic-map" style="width:100%;height:560px;border-radius:8px;"></div>
<div id="mappls-traffic-error" style="color:#d8453c;font-family:monospace;white-space:pre-wrap;"></div>
<script src="https://sdk.mappls.com/map/sdk/web?v=3.0&access_token={api_key}&callback=initTrafficMap"></script>
<script>
function initTrafficMap() {{
    try {{
        var map = new mappls.Map('mappls-traffic-map', {{
            center: {{lat: {center_lat}, lng: {center_lon}}},
            zoom: {zoom},
            traffic: true
        }});
        map.on('load', function() {{
            try {{
                {marker_script}
            }} catch (markerError) {{
                document.getElementById('mappls-traffic-error').innerText = 'Marker error: ' + markerError.message;
            }}
        }});
    }} catch (mapError) {{
        document.getElementById('mappls-traffic-error').innerText = 'Map init error: ' + mapError.message;
    }}
}}
</script>
"""
    return html


def build_route_map_html(api_key, markers):
    marker_script = build_marker_script(markers)
    markers_json = json.dumps(markers)

    html = f"""
<div id="mappls-route-map" style="width:100%;height:560px;border-radius:8px;"></div>
<div id="mappls-route-status" style="color:#6b7280;font-family:monospace;font-size:12px;white-space:pre-wrap;margin-top:6px;"></div>
<script src="https://sdk.mappls.com/map/sdk/web?v=3.0&access_token={api_key}&callback=initRouteMap"></script>
<script>
var routeMarkers = {markers_json};

function decodePolyline(encoded, precision) {{
    if (!encoded) {{
        return [];
    }}
    var coordinates = [];
    var index = 0;
    var lat = 0;
    var lng = 0;
    var factor = Math.pow(10, precision || 5);

    while (index < encoded.length) {{
        var result = 1;
        var shift = 0;
        var b;
        do {{
            b = encoded.charCodeAt(index++) - 63 - 1;
            result += b << shift;
            shift += 5;
        }} while (b >= 0x1f);
        lat += (result & 1) !== 0 ? ~(result >> 1) : (result >> 1);

        result = 1;
        shift = 0;
        do {{
            b = encoded.charCodeAt(index++) - 63 - 1;
            result += b << shift;
            shift += 5;
        }} while (b >= 0x1f);
        lng += (result & 1) !== 0 ? ~(result >> 1) : (result >> 1);

        coordinates.push({{lat: lat / factor, lng: lng / factor}});
    }}

    return coordinates;
}}

function straightLinePath() {{
    return routeMarkers.map(function(marker) {{
        return {{lat: marker.lat, lng: marker.lon}};
    }});
}}

function drawRoute(map, path, color, label) {{
    new mappls.Polyline({{
        map: map,
        path: path,
        strokeColor: color,
        strokeWeight: 4,
        fitbounds: true
    }});
    document.getElementById('mappls-route-status').innerText = label;
}}

function drawFallbackRoute(map, reason) {{
    drawRoute(
        map,
        straightLinePath(),
        '#d8453c',
        'Showing straight-line stop order. Browser-side routing was unavailable: ' + reason
    );
}}

async function loadBrowserRoute(map) {{
    var coords = routeMarkers.map(function(marker) {{
        return marker.lon + ',' + marker.lat;
    }}).join(';');
    var url = 'https://apis.mappls.com/advancedmaps/v1/{api_key}/route_adv/driving/' + coords + '?geometries=polyline&overview=full&steps=false';

    try {{
        var response = await fetch(url);
        if (!response.ok) {{
            var errorBody = await response.text();
            drawFallbackRoute(map, 'HTTP ' + response.status + ': ' + errorBody.slice(0, 180));
            return;
        }}

        var payload = await response.json();
        if (!payload.routes || !payload.routes.length || !payload.routes[0].geometry) {{
            drawFallbackRoute(map, 'no route geometry returned');
            return;
        }}

        var path = decodePolyline(payload.routes[0].geometry, 5);
        if (!path.length) {{
            drawFallbackRoute(map, 'route geometry decoded to zero points');
            return;
        }}

        drawRoute(map, path, '#2563eb', 'Road-following route rendered with browser-side Mappls routing');
    }} catch (error) {{
        drawFallbackRoute(map, error.message);
    }}
}}

function initRouteMap() {{
    var statusBox = document.getElementById('mappls-route-status');
    try {{
        var map = new mappls.Map('mappls-route-map', {{
            center: {{lat: {markers[0]['lat']}, lng: {markers[0]['lon']}}},
            zoom: 12
        }});
        map.on('load', function() {{
            try {{
                {marker_script}
            }} catch (markerError) {{
                statusBox.innerText = 'Marker rendering failed: ' + markerError.message;
                return;
            }}
            loadBrowserRoute(map);
        }});
    }} catch (mapError) {{
        statusBox.innerText = 'Map initialization failed: ' + mapError.message;
    }}
}}
</script>
"""
    return html
