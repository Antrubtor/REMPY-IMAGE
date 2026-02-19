import streamlit as st
import requests
import json
import numpy as np
from PIL import Image
from benchmark import plot_bar, plot_scatter, plot_image

st.set_page_config(page_title="REMPY-IMAGE", layout="wide")
BACKEND_URL = "http://backend:8000"

st.title("🔥 REMPY-IMAGE")
st.markdown("Frontend Streamlit - Geodesic Distance Transform")

st.sidebar.header("📁 Uploads")
image_file = st.sidebar.file_uploader("Image (JPEG/PNG)", type=['jpeg', 'png'])
mask_file = st.sidebar.file_uploader("Mask (PNG)", type=['png'])
nb_tests = st.sidebar.number_input("Tests", min_value=1, value=10)

if image_file:
    image_bytes = image_file.getvalue()
    st.sidebar.image(image_bytes, caption="Image", width=200)
if mask_file:
    mask_bytes = mask_file.getvalue()
    st.sidebar.image(mask_bytes, caption="Mask", width=200)

if st.sidebar.button("🚀 Start Benchmark", type="primary"):
    if image_file and mask_file:
        with st.spinner("Benchmark..."):
            image_bytes = image_file.getvalue()
            mask_bytes = mask_file.getvalue()

            files = {
                'image': ('image.jpg', image_bytes, 'image/jpeg'),
                'mask': ('mask.png', mask_bytes, 'image/png')
            }

            try:
                resp_hash = requests.post(f"{BACKEND_URL}/benchmark/hash", 
                                        files=files, timeout=30)
                
                if resp_hash.status_code == 200:
                    benchmark_data = resp_hash.json()
                    benchmark_id = benchmark_data["benchmark_id"]
                    
                    resp_results = requests.get(f"{BACKEND_URL}/benchmark?id={benchmark_id}")
                    if resp_results.status_code == 200:
                        results = resp_results.json()
                        st.json(f"1| {results}")
                    else:
                        raise Exception(f"Erreur récupération: {resp_results.text}")
                        
                else:
                    resp_benchmark = requests.post(
                        f"{BACKEND_URL}/benchmarks/run?nb_tests={nb_tests}", 
                        files=files, timeout=60
                    )
                    
                    if resp_benchmark.status_code != 200:
                        raise Exception(f"Erreur backend: {resp_benchmark.text}")
                    
                    results = resp_benchmark.json()
                    st.json(f"2| {results}")

                if "benchmarks" in results and results['benchmarks']:
                    python_times = [b['python_time'] for b in results['benchmarks']]
                    numba_times = [b['numba_time'] for b in results['benchmarks']]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Python", f"{np.mean(python_times):.3f}s")
                    with col2:
                        st.metric("Numba", f"{np.mean(numba_times):.3f}s")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.plotly_chart(plot_bar(json.dumps(results)), use_container_width=True, key="bar_chart")
                    with col2:
                        st.plotly_chart(plot_scatter(json.dumps(results)), use_container_width=True, key="scatter_chart")
                    with col3:
                        st.plotly_chart(plot_image(json.dumps(results)), use_container_width=True, key="image_chart")
                        
                else:
                    st.error(f"Pas de données 'benchmarks' {results}")
                    
            except Exception as e:
                st.error(f"Erreur: {e}")
    else:
        st.sidebar.warning("Upload image + mask")
