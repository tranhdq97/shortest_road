import os
from itertools import permutations
from math import atan2, degrees

import folium
import numpy as np
import polyline
import requests
from shortest_road.settings import env, BASE_DIR


class GoogleMapAPIException(Exception):
    pass


class ShortestRoadToMultiPoints:
    def __init__(self):
        self._api_key = env.str("GOOGLE_MAPS_API_KEY")
        self._start_color = "green"
        self._end_color = "red"

    def _get_coordinates(self, address: str):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={self._api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            raise GoogleMapAPIException(
                f"Error: {response.status_code}, {response.text}"
            )
        data = response.json()
        if "results" not in data or len(data["results"]) == 0:
            raise GoogleMapAPIException(f"No results found for address: {address}")
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]

    def _get_distance_matrix(self, locations: list[str], mode="driving"):
        origins = "|".join(locations)
        destinations = "|".join(locations)
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origins}&destinations={destinations}&mode={mode}&key={self._api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            raise GoogleMapAPIException(
                f"Error: {response.status_code}, {response.text}"
            )
        return response.json()

    def _get_directions(self, origin: str, destination: str, mode="driving"):
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&mode={mode}&avoid=tolls|highways&key={self._api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            raise GoogleMapAPIException(
                f"Error: {response.status_code}, {response.text}"
            )
        return response.json()

    def _plot_route_on_map(self, locations: list, path: tuple, mode: str = "driving"):
        num_path = len(path)
        gradient_colors = self._get_gradient_color(n_steps=num_path)
        start_lat, start_lng = locations[path[0]]
        m = folium.Map(location=[start_lat, start_lng], zoom_start=12)
        for i in range(num_path):
            start = locations[path[i]]
            end = locations[path[(i + 1) % len(path)]]
            start_str = f"{start[0]},{start[1]}"
            end_str = f"{end[0]},{end[1]}"
            directions = self._get_directions(start_str, end_str, mode)
            route = directions["routes"][0]["overview_polyline"]["points"]
            points = folium.PolyLine(
                locations=self._decode_polyline(route),
                color=gradient_colors[i],
                weight=2.5,
                opacity=1,
            )
            m.add_child(points)

        for idx, point in enumerate(path):
            folium.Marker(
                location=[locations[point][0], locations[point][1]],
                icon=folium.Icon(icon="carrot", prefix="fa"),
                popup=f"Point {idx + 1}",
                tooltip=f"Point {idx + 1}",
            ).add_to(m)
        folium.Marker(
            location=[start_lat, start_lng],
            popup="Start",
            icon=folium.Icon(color="green"),
        ).add_to(m)
        folium.Marker(
            location=[locations[path[-1]][0], locations[path[-1]][1]],
            popup="End",
            icon=folium.Icon(color="red"),
        ).add_to(m)
        m.save(f"{BASE_DIR}/templates/map.html")

    def _get_gradient_color(self, n_steps: int):
        from matplotlib import colors as m_colors

        gradient = self._gradient_color(
            start_color=self._start_color, end_color=self._end_color, n_steps=n_steps
        )
        return [m_colors.rgb2hex(color) for color in gradient]

    def handle(self, locations: list[str]):
        coords = [self._get_coordinates(address=location) for location in locations]
        distance_matrix = self._get_distance_matrix(locations=locations)
        distances = self._extract_distances(distance_matrix)
        path, _ = self._solve_tsp(distances)
        self._plot_route_on_map(locations=coords, path=path, mode="driving")

    @staticmethod
    def _calculate_angle(start, end):
        lat1, lon1 = start
        lat2, lon2 = end
        angle = atan2(lat2 - lat1, lon2 - lon1)
        return degrees(angle)

    @staticmethod
    def _gradient_color(start_color: str, end_color: str, n_steps: int):
        from matplotlib import colors as m_colors

        start_rgb = m_colors.hex2color(start_color)
        end_rgb = m_colors.hex2color(end_color)

        r = np.linspace(start_rgb[0], end_rgb[0], n_steps)
        g = np.linspace(start_rgb[1], end_rgb[1], n_steps)
        b = np.linspace(start_rgb[2], end_rgb[2], n_steps)

        return [
            (max(min(1, red), 0), max(min(1, green), 0), max(min(1, blue), 0))
            for red, green, blue in zip(r, g, b)
        ]

    @staticmethod
    def _extract_distances(distance_matrix: dict):
        distances = []
        rows = distance_matrix["rows"]
        for row in rows:
            distances.append(
                [element["distance"]["value"] for element in row["elements"]]
            )
        return distances

    @staticmethod
    def _solve_tsp(distances: list[list[float]]):
        n = len(distances)
        min_path = None
        min_distance = float("inf")
        for perm in permutations(range(n)):
            current_distance = sum(
                distances[perm[i]][perm[i + 1]] for i in range(n - 1)
            )
            current_distance += distances[perm[-1]][perm[0]]  # Return to start
            if current_distance < min_distance:
                min_distance = current_distance
                min_path = perm
        return min_path, min_distance

    @staticmethod
    def _decode_polyline(polyline_str: str):
        return polyline.decode(polyline_str)
