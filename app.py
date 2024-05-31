from flask import Flask, render_template, request, make_response

from service.shortest_road_to_multi_points import ShortestRoadToMultiPoints

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    current_location = data["current_location"]
    destinations = data["destinations"]
    locations = [current_location] + destinations
    shortest_road = ShortestRoadToMultiPoints()
    shortest_road.handle(locations=locations)
    return make_response({}, 200)


@app.route("/map_display", methods=["GET"])
def map_display():
    return render_template("map_display.html")


if __name__ == "__main__":
    app.run(debug=True)
