import json
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import streamlit as st


def plot_bar(benchmarks: str) -> go.Figure:
    data = json.loads(benchmarks).get("benchmarks", [])

    # Flatten tous benchmarks_times de tous items
    all_times = []
    for benchmark in data:
        for i, time_data in enumerate(benchmark.get("benchmark_times", [])):
            all_times.append({
                "id": i + 1,
                "python_time": time_data.get("python_time", 0),
                "numba_time": time_data.get("numba_time", 0)
            })
    
    if not all_times:
        return go.Figure().add_annotation(text="Aucun benchmark")
    
    # Prends derniers 10
    plot_data = sorted(all_times, key=lambda x: x["id"])[-10:]
    
    ids = [t["id"] for t in plot_data]
    times_python = [t["python_time"] for t in plot_data]
    times_numba = [t["numba_time"] for t in plot_data]

    fig = go.Figure(data=[
        go.Bar(name='Python', x=ids, y=times_python, marker_color='lightblue'),
        go.Bar(name='Numba', x=ids, y=times_numba, marker_color='orange')
    ])
    
    fig.update_layout(
        title="Python vs Numba (Bar)",
        xaxis_title="Benchmark ID", 
        yaxis_title="Temps (s)",
        barmode="group"
    )
    return fig


def plot_scatter(benchmarks: str) -> go.Figure:
    data = json.loads(benchmarks).get("benchmarks", [])

    # Même flatten
    all_times = []
    for benchmark in data:
        for i, time_data in enumerate(benchmark.get("benchmark_times", [])):
            all_times.append({
                "id": i + 1,
                "python_time": time_data.get("python_time", 0),
                "numba_time": time_data.get("numba_time", 0)
            })
    
    if not all_times:
        return go.Figure().add_annotation(text="Aucun benchmark")
    
    plot_data = sorted(all_times, key=lambda x: x["id"])[-10:]
    
    ids = [t["id"] for t in plot_data]
    times_python = [t["python_time"] for t in plot_data]
    times_numba = [t["numba_time"] for t in plot_data]

    fig = go.Figure(data=[
        go.Scatter(name='Python', x=ids, y=times_python, mode="lines+markers"),
        go.Scatter(name='Numba', x=ids, y=times_numba, mode="lines+markers")
    ])
    
    fig.update_layout(
        title="Python vs Numba (Scatter)",
        xaxis_title="Benchmark ID", 
        yaxis_title="Temps (s)"
    )
    return fig


def plot_image(image_json: str) -> go.Figure:
    try:
        data = json.loads(image_json)
        
        # Cherche image_result dans benchmarks[0]
        image_result = data.get("benchmarks", [{}])[0].get("image_result", [])
        
        if image_result and len(image_result) > 0:
            image = np.array(image_result)
            
            # Auto-reshape si 1D
            if image.ndim == 1:
                size = int(np.sqrt(len(image)))
                if size * size == len(image):
                    image = image.reshape((size, size))
            
            fig = px.imshow(
                image,
                color_continuous_scale='inferno',
                range_color=[image.min(), image.max()],
                title=f"Distance Map ({image.shape})"
            )
            fig.update_layout(coloraxis_colorbar=dict(title="Distance"))
            return fig
    except Exception as e:
        print(f"Erreur plot_image: {e}")

    return go.Figure().add_annotation(text="Pas d'image_result")
