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

if 'benchmark_exists' not in st.session_state:
    st.session_state.benchmark_exists = False
if 'benchmark_id' not in st.session_state:
    st.session_state.benchmark_id = None

if st.sidebar.button("🚀 Start Benchmark", type="primary"):
    if image_file and mask_file:
        st.session_state.show_results = False
        st.session_state.benchmark_exists = False
        
        image_bytes = image_file.getvalue()
        mask_bytes = mask_file.getvalue()
        files = {
            'image': ('image.jpg', image_bytes, 'image/jpeg'),
            'mask': ('mask.png', mask_bytes, 'image/png')
        }

        resp_hash = requests.post(f"{BACKEND_URL}/benchmark/hash", files=files, timeout=30)
        
        if resp_hash.status_code == 200:
            st.session_state.benchmark_exists = True
            st.session_state.benchmark_id = resp_hash.json()["benchmark_id"]
            st.success("✅ Benchmark found in database!")
        else:
            st.session_state.benchmark_exists = False
            st.info("🆕 Running new benchmark...")
            resp_benchmark = requests.post(
                f"{BACKEND_URL}/benchmarks/run?nb_tests={nb_tests}", 
                files=files, timeout=60
            )
            if resp_benchmark.status_code == 200:
                st.session_state.results = resp_benchmark.json()
                st.session_state.show_results = True
            else:
                st.error(f"Backend error: {resp_benchmark.text}")

if st.session_state.benchmark_exists:
    st.markdown("---")
    st.header("⚠️ Existing Benchmark")
    st.info(f"Benchmark ID: {st.session_state.benchmark_id}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 View existing results"):
            resp_results = requests.get(f"{BACKEND_URL}/benchmark?id={st.session_state.benchmark_id}")
            if resp_results.status_code == 200:
                st.session_state.results = resp_results.json()
                st.session_state.show_results = True
                st.session_state.benchmark_exists = False
                st.rerun()
    with col2:
        if st.button("➕ Add more runs"):
            image_bytes = image_file.getvalue()
            mask_bytes = mask_file.getvalue()
            files = {
                'image': ('image.jpg', image_bytes, 'image/jpeg'),
                'mask': ('mask.png', mask_bytes, 'image/png')
            }
            resp_benchmark = requests.post(
                f"{BACKEND_URL}/benchmarks/run?nb_tests={nb_tests}", 
                files=files, timeout=60
            )
            if resp_benchmark.status_code == 200:
                st.session_state.results = resp_benchmark.json()
                st.session_state.show_results = True
                st.session_state.benchmark_exists = False
                st.rerun()

if st.session_state.get('show_results') and st.session_state.get('results'):
    st.markdown("---")
    st.header("📊 Results")

    results = st.session_state.results

    if "benchmarks" in results and results['benchmarks']:
        python_times = []
        numba_times = []
        
        for benchmark in results['benchmarks']:
            if 'benchmark_times' in benchmark:
                for t in benchmark['benchmark_times']:
                    python_times.append(t['python_time'])
                    numba_times.append(t['numba_time'])
            else:
                python_times.append(benchmark.get('python_time', 0))
                numba_times.append(benchmark.get('numba_time', 0))

        speedup_mean = np.mean(python_times) / np.mean(numba_times)
        speedup_min = np.min(python_times) / np.max(numba_times) 
        speedup_max = np.max(python_times) / np.min(numba_times)
        speedup_std = np.std(np.array(python_times) / np.array(numba_times))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Python Mean", f"{np.mean(python_times):.3f}s")
            st.metric("Python Min/Max", f"{np.min(python_times):.3f}s / {np.max(python_times):.3f}s")
            st.metric("Python Std", f"{np.std(python_times):.3f}s")
        with col2:
            st.metric("Numba Mean", f"{np.mean(numba_times):.3f}s")
            st.metric("Numba Min/Max", f"{np.min(numba_times):.3f}s / {np.max(numba_times):.3f}s")
            st.metric("Numba Std", f"{np.std(numba_times):.3f}s")
        with col3:
            st.metric("🚀 Speedup Mean", "", delta=None, delta_color="normal")
            st.success(f"{speedup_mean:.2f}x")
            st.metric("Speedup Min/Max", "")
            st.success(f"{speedup_min:.2f}x - {speedup_max:.2f}x")
            st.metric("Speedup Std", "")
            st.success(f"{speedup_std:.2f}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(plot_bar(json.dumps(results)), use_container_width=True, key="bar")
        with col2:
            st.plotly_chart(plot_scatter(json.dumps(results)), use_container_width=True, key="scatter")
        with col3:
            st.plotly_chart(plot_image(json.dumps(results)), use_container_width=True, key="image")
    else:
        st.warning("No benchmark data")
