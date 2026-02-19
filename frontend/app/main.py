import streamlit as st
import base64
import io
import requests
import json
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image

# IMPORT FONCTIONS depuis benchmark.py (même dossier)
from benchmark import plot_bar, plot_scatter, plot_image  # ← Vos fonctions existantes !

# Config
st.set_page_config(page_title="REMPY-IMAGE", layout="wide")
BACKEND_URL = "http://backend:8000"

st.title("🔥 REMPY-IMAGE")
st.markdown("Frontend Streamlit - Geodesic Distance Transform")

# Sidebar
st.sidebar.header("📁 Uploads")
image_file = st.sidebar.file_uploader("Image (JPEG/PNG)", type=['jpeg', 'png'])
mask_file = st.sidebar.file_uploader("Mask (PNG)", type=['png'])

nb_tests = st.sidebar.number_input("Tests", min_value=1, value=10)

if st.sidebar.button("🚀 Start Benchmark", type="primary"):
    if image_file and mask_file:
        with st.spinner("Benchmark..."):
            image_bytes = image_file.read()
            mask_bytes = mask_file.read()
            
            files = {
                'image': ('image.jpg', image_bytes, 'image/jpeg'),
                'mask': ('mask.png', mask_bytes, 'image/png')
            }
            data = {'nb_tests': nb_tests}
            
            try:
                resp = requests.post(f"{BACKEND_URL}/benchmarks", files=files, data=data)
                resp.raise_for_status()
                results = resp.json()
                
                # Metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Python", f"{np.mean([b['python_time'] for b in results['benchmarks']]):.3f}s")
                with col2:
                    st.metric("Numba", f"{np.mean([b['numba_time'] for b in results['benchmarks']]):.3f}s")
                
                # Plots (vos fonctions importées !)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.plotly_chart(plot_bar(json.dumps(results)), use_container_width=True)
                with col2:
                    st.plotly_chart(plot_scatter(json.dumps(results)), use_container_width=True)
                with col3:
                    st.plotly_chart(plot_image(json.dumps(results)), use_container_width=True)
                
            except Exception as e:
                st.error(f"Erreur: {e}")
    else:
        st.sidebar.warning("Upload image + mask")

# Aperçu images uploadées
if image_file:
    st.sidebar.image(Image.open(io.BytesIO(image_file.read())), caption="Image", width=200)
if mask_file:
    st.sidebar.image(Image.open(io.BytesIO(mask_file.read())), caption="Mask", width=200)

