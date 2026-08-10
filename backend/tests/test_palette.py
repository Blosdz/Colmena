from fastapi.testclient import TestClient

from app.charts.palette import random_bar_colors


def test_palette_colors_are_distinct_and_hex():
    colors = random_bar_colors(8)

    assert len(colors) == 8
    # Repartir los tonos sobre la rueda garantiza que no se repita ninguno.
    assert len(set(colors)) == 8
    assert all(len(color) == 7 and color.startswith("#") for color in colors)
    assert all(int(color[1:], 16) >= 0 for color in colors)


def test_palette_is_reproducible_with_seed():
    assert random_bar_colors(5, seed="grafico-1") == random_bar_colors(5, seed="grafico-1")
    assert random_bar_colors(5, seed="grafico-1") != random_bar_colors(5, seed="grafico-2")


def test_palette_endpoint(client: TestClient):
    response = client.get("/api/v1/charts/palette", params={"count": 3})

    assert response.status_code == 200
    assert len(response.json()["colors"]) == 3


def test_palette_endpoint_accepts_zero(client: TestClient):
    response = client.get("/api/v1/charts/palette", params={"count": 0})

    assert response.status_code == 200
    assert response.json()["colors"] == []
