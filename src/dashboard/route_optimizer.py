import math

from src import config


def haversine_km(point_a, point_b):
    lat1 = math.radians(float(point_a["lat"]))
    lon1 = math.radians(float(point_a["lon"]))
    lat2 = math.radians(float(point_b["lat"]))
    lon2 = math.radians(float(point_b["lon"]))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c


def route_distance_km(points):
    if len(points) < 2:
        return 0.0
    return sum(haversine_km(points[index], points[index + 1]) for index in range(len(points) - 1))


def nearest_neighbor_route(points):
    if len(points) <= 2:
        return list(points)
    remaining = list(points[1:])
    route = [points[0]]
    while remaining:
        current = route[-1]
        next_index = min(
            range(len(remaining)),
            key=lambda index: haversine_km(current, remaining[index]),
        )
        route.append(remaining.pop(next_index))
    return route


def two_opt(points):
    best = list(points)
    best_distance = route_distance_km(best)
    improved = True

    while improved:
        improved = False
        for start in range(1, len(best) - 2):
            for end in range(start + 1, len(best) - 1):
                candidate = best[:start] + list(reversed(best[start : end + 1])) + best[end + 1 :]
                candidate_distance = route_distance_km(candidate)
                if candidate_distance + 0.01 < best_distance:
                    best = candidate
                    best_distance = candidate_distance
                    improved = True
        points = best

    return best


def optimize_waypoint_order(points):
    ordered = nearest_neighbor_route(points)
    ordered = two_opt(ordered)
    distance_km = route_distance_km(ordered)
    eta_minutes = distance_km / max(config.ROUTE_SPEED_KMPH, 1.0) * 60.0
    return ordered, distance_km, eta_minutes
