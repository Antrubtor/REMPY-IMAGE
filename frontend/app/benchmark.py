import json
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


def plot_bar(benchmarks: str) -> go.Figure:
    benchmarks = json.loads(benchmarks).get("benchmarks", [])

    for i, b in enumerate(benchmarks):
        if "id" not in b:
            b["id"] = i

    data = sorted(benchmarks, key=lambda b: b["id"])[-10:]

    ids = [b["id"] for b in data]
    times_python = [b["python_time"] for b in data]
    times_numba = [b["numba_time"] for b in data]

    fig = go.Figure(data=[
        go.Bar(name='Python', x=ids, y=times_python),
        go.Bar(name='Numba', x=ids, y=times_numba)
    ])

    fig.update_layout(
        title="Geodesic Distance Transform Python / Numba",
        xaxis_title="ID benchmark",
        yaxis_title="Temps (s)",
        barmode="group",
    )

    return fig

def plot_scatter(benchmarks: str) -> go.Figure:
    benchmarks = json.loads(benchmarks).get("benchmarks", [])
 
    for i, b in enumerate(benchmarks):
        if "id" not in b:
            b["id"] = i

    data = sorted(benchmarks, key=lambda b: b["id"])[-10:]

    ids = [b["id"] for b in data]
    times_python = [b["python_time"] for b in data]
    times_numba = [b["numba_time"] for b in data]

    fig = go.Figure(data=[
        go.Scatter(name='Python', x=ids, y=times_python, mode="lines+markers"),
        go.Scatter(name='Numba', x=ids, y=times_numba, mode="lines+markers")
    ])

    fig.update_layout(
        title="Geodesic Distance Transform Python / Numba",
        xaxis_title="ID benchmark",
        yaxis_title="Temps (s)",
        barmode="group",
    )

    return fig

def plot_image(image_json: str) -> go.Figure:
    try:
        data = json.loads(image_json).get("image_result", [])
        if data and len(data) > 0:
            image = np.array(data)
            
            fig = px.imshow(
                image,
                color_continuous_scale='inferno',
                range_color=[image.min(), image.max()],
                title="Geodesic Distance Transform (Inferno)"
            )
            fig.update_layout(
                coloraxis_colorbar=dict(
                    title="Distance", 
                    titleside="right"
                )
            )
            return fig
    except:
        pass
    
    return go.Figure().add_annotation(text="Pas d'image")