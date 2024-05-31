from itertools import permutations

import folium
import polyline
import requests
import os

from dotenv import load_dotenv


def get_coordinates(address, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    data = response.json()
    if 'results' not in data or len(data['results']) == 0:
        raise Exception(f"No results found for address: {address}")
    location = data['results'][0]['geometry']['location']
    return (location['lat'], location['lng'])


def get_distance_matrix(locations, api_key, mode='driving'):
    origins = "|".join(locations)
    destinations = "|".join(locations)
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origins}&destinations={destinations}&mode={mode}&key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    return response.json()


def extract_distances(distance_matrix):
    distances = []
    rows = distance_matrix['rows']
    for row in rows:
        distances.append([element['distance']['value'] for element in row['elements']])
    return distances


def solve_tsp(distances):
    n = len(distances)
    min_path = None
    min_distance = float('inf')
    for perm in permutations(range(n)):
        current_distance = sum(distances[perm[i]][perm[i + 1]] for i in range(n - 1))
        current_distance += distances[perm[-1]][perm[0]]  # Return to start
        if current_distance < min_distance:
            min_distance = current_distance
            min_path = perm
    return min_path, min_distance


def get_directions(origin, destination, api_key, mode='driving'):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&mode={mode}&avoid=tolls|highways&key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    return response.json()


def decode_polyline(polyline_str):
    return polyline.decode(polyline_str)


def plot_route_on_map(locations, path, api_key, mode='driving'):
    # Tạo bản đồ tại vị trí xuất phát
    start_lat, start_lng = locations[path[0]]
    m = folium.Map(location=[start_lat, start_lng], zoom_start=12)

    # Vẽ tuyến đường
    for i in range(len(path)):
        start = locations[path[i]]
        end = locations[path[(i + 1) % len(path)]]
        start_str = f"{start[0]},{start[1]}"
        end_str = f"{end[0]},{end[1]}"
        directions = get_directions(start_str, end_str, api_key, mode)
        route = directions['routes'][0]['overview_polyline']['points']
        points = folium.PolyLine(locations=decode_polyline(route), color="blue", weight=2.5, opacity=1)
        m.add_child(points)

    # Thêm điểm bắt đầu và kết thúc với số thứ tự
    for idx, point in enumerate(path):
        folium.Marker(location=[locations[point][0], locations[point][1]], popup=f"Point {idx + 1}",
                      icon=folium.Icon(color='blue')).add_to(m)

    folium.Marker(location=[start_lat, start_lng], popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=[locations[path[-1]][0], locations[path[-1]][1]], popup="End",
                  icon=folium.Icon(color='red')).add_to(m)

    # Lưu và hiển thị bản đồ
    m.save("map.html")
    print("Map has been saved to map.html")


def main():
    # Thông tin về các địa điểm và API key
    locations = ["Hoa Lien, Hoa Vang, Da Nang", "Hoa Khanh Bac, Lien Chieu Da Nang", "Ton Dan, Cam Le, Da Nang",
                 "Tam Ky, Quang Nam"]
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # Chuyển đổi địa chỉ thành tọa độ
    coords = [get_coordinates(location, api_key) for location in locations]

    # Lấy ma trận khoảng cách từ Google Maps API cho phương tiện xe máy
    distance_matrix = get_distance_matrix(locations, api_key, mode='driving')

    # Trích xuất khoảng cách
    distances = extract_distances(distance_matrix)

    # Giải quyết bài toán TSP
    path, min_distance = solve_tsp(distances)

    # In kết quả
    print("Optimal path:", path)
    print("Minimum distance:", min_distance)

    # Hiển thị tuyến đường trên bản đồ
    plot_route_on_map(coords, path, api_key, mode='driving')


if __name__ == "__main__":
    main()
