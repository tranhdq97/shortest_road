from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse

from shortest_road.service import ShortestRoadToMultiPoints


def index(request):
    return render(request, "index.html")


def calculate(request):
    if request.method == "POST":
        current_location = request.POST.get("current_location")
        destinations = request.POST.getlist("destinations")
        locations = [current_location] + destinations
        shortest_road = ShortestRoadToMultiPoints()
        shortest_road.handle(locations=locations)
        # Redirect to the display_map view after processing the form
        return HttpResponseRedirect(
            reverse("display_map")
        )  # Use reverse with the URL pattern name
    return render(request, "index.html")


def display_map(request):
    return render(request, "map.html")
