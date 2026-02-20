import streamlit as st
import requests
import json
import numpy as np
from PIL import Image
from benchmark import plot_bar, plot_scatter, plot_image
import io
import base64

def decode_array(b64str: str) -> np.ndarray:
    if not isinstance(b64str, str) or not b64str:
        return np.array([])
    b = base64.b64decode(b64str)
    return np.load(io.BytesIO(b))

st.set_page_config(page_title="REMPY-IMAGE", layout="wide")
BACKEND_URL = "http://backend:8000"

# Global navigation state
if 'page' not in st.session_state:
    st.session_state.page = "Accueil"

# Sidebar Navigation
st.sidebar.title("Navigation")
if st.sidebar.button("Home", use_container_width=True):
    st.session_state.page = "Accueil"
    st.session_state.benchmark_exists = False
    st.session_state.show_results = False
    st.session_state.results = None
    st.rerun()

if st.sidebar.button("History", use_container_width=True):
    st.session_state.page = "Historique"
    st.session_state.benchmark_exists = False
    st.session_state.show_results = False
    st.session_state.results = None
    st.rerun()

# State initialization
if 'benchmark_exists' not in st.session_state:
    st.session_state.benchmark_exists = False
if 'benchmark_id' not in st.session_state:
    st.session_state.benchmark_id = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False
if 'loading' not in st.session_state:
    st.session_state.loading = False

def reset_benchmark_state():
    st.session_state.benchmark_exists = False
    st.session_state.show_results = False
    st.session_state.results = None

# Home Page
if st.session_state.page == "Accueil":
    st.title("REMPY-IMAGE")
    st.markdown("Geodesic Distance Transform")
    
    st.sidebar.header("Uploads")
    image_file = st.sidebar.file_uploader("Image (JPEG/PNG)", type=['jpeg', 'png'], key="image_uploader", on_change=reset_benchmark_state)
    mask_file = st.sidebar.file_uploader("Mask (PNG)", type=['png'], key="mask_uploader", on_change=reset_benchmark_state)
    
    if st.session_state.benchmark_exists:
        if st.sidebar.button("📊 View existing results", use_container_width=True):
            st.session_state.loading = True
            st.session_state._action = "view"
            st.session_state.show_results = False
            st.rerun()
        if not image_file or not mask_file:
            st.sidebar.info(f"Ready to add runs to Benchmark #{st.session_state.get('benchmark_id')}. Choose the number of tests and click Start.")
        else:
            st.sidebar.info("A benchmark already exists for these images. Starting a new benchmark will add the runs to the existing ones.")
        
    nb_tests = st.sidebar.number_input("Tests", min_value=1, value=10, key="nb_tests")
    
    if image_file:
        image_bytes = image_file.getvalue()
        image = Image.open(io.BytesIO(image_bytes)).convert('L')
        image_pil = Image.open(io.BytesIO(image_file.getvalue())).convert('L')
        image_file = io.BytesIO()
        image_pil.save(image_file, format='JPEG', quality=95)
        st.sidebar.image(image, caption="Image", width=200, clamp=True)
    
    if mask_file:
        mask_bytes = mask_file.getvalue()
        st.sidebar.image(mask_bytes, caption="Mask", width=200)
    
    if st.sidebar.button("Start Benchmark", type="primary"):
        if st.session_state.benchmark_exists:
            st.session_state.loading = True
            st.session_state._action = "add_runs"
            st.session_state.show_results = False
            st.rerun()
        elif image_file and mask_file:
            st.session_state.show_results = False
            st.session_state.benchmark_exists = False
            
            image_bytes = image_file.getvalue()
            mask_bytes = mask_file.getvalue()
            files = {
                'image': ('image.jpg', image_bytes, 'image/jpeg'),
                'mask': ('mask.png', mask_bytes, 'image/png')
            }
            
            with st.spinner("Checking hash..."):
                resp_hash = requests.post(f"{BACKEND_URL}/benchmark/hash", files=files, timeout=30)
            
            if resp_hash.status_code == 200:
                st.session_state.benchmark_exists = True
                st.session_state.benchmark_id = resp_hash.json()["benchmark_id"]
                st.rerun()
            else:
                st.session_state.benchmark_exists = False
                with st.spinner("Running benchmark..."):
                    resp_benchmark = requests.post(
                        f"{BACKEND_URL}/benchmarks/run?nb_tests={nb_tests}",
                        files=files
                    )
                if resp_benchmark.status_code == 200:
                    st.session_state.results = resp_benchmark.json()
                    st.session_state.show_results = True
                else:
                    st.error(f"Backend error: {resp_benchmark.text}")
    
    # Middle buttons section removed as requested

    
    # Handle deferred loading actions
    if st.session_state.loading and st.session_state.benchmark_exists:
        action = st.session_state.get('_action', 'view')
        
        if action == "add_runs":
            with st.spinner("Adding runs..."):
                if image_file and mask_file:
                    image_bytes = image_file.getvalue()
                    mask_bytes = mask_file.getvalue()
                    files = {
                        'image': ('image.jpg', image_bytes, 'image/jpeg'),
                        'mask': ('mask.png', mask_bytes, 'image/png')
                    }
                    resp_benchmark = requests.post(
                        f"{BACKEND_URL}/benchmarks/run?nb_tests={nb_tests}",
                        files=files
                    )
                else:
                    resp_benchmark = requests.post(
                        f"{BACKEND_URL}/benchmarks/run_by_id?benchmark_id={st.session_state.benchmark_id}&nb_tests={nb_tests}"
                    )
            if resp_benchmark.status_code == 200:
                st.session_state.results = resp_benchmark.json()
                st.session_state.show_results = True
                st.session_state.benchmark_exists = False
                st.session_state.loading = False
                st.session_state._action = None
                st.rerun()
        else:
            with st.spinner("Loading results..."):
                resp_results = requests.get(f"{BACKEND_URL}/benchmark?id={st.session_state.benchmark_id}")
            if resp_results.status_code == 200:
                st.session_state.results = resp_results.json()
                st.session_state.show_results = True
                st.session_state.benchmark_exists = False
                st.session_state.loading = False
                st.session_state._action = None
                st.rerun()
    
    # Results display
    if st.session_state.get('show_results') and st.session_state.get('results'):
        st.markdown("---")
        st.header("Results")
        
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
                st.metric("Speedup Mean", f"{speedup_mean:.2f}x")
                st.metric("Speedup Min/Max", f"{speedup_min:.2f}x - {speedup_max:.2f}x")
                st.metric("Speedup Std", f"{speedup_std:.2f}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(plot_bar(json.dumps(results)), use_container_width=True, key="bar")
            with col2:
                st.plotly_chart(plot_scatter(json.dumps(results)), use_container_width=True, key="scatter")
            with col3:
                st.plotly_chart(plot_image(json.dumps(results)), use_container_width=True, key="image")
        else:
            st.warning("No benchmark data")

# History Page
elif st.session_state.page == "Historique":
    st.title("Benchmark History")
    st.markdown("All image + mask combinations previously benchmarked")

    try:
        with st.spinner("Loading history..."):
            resp_benchmarks = requests.get(f"{BACKEND_URL}/benchmarks")
        if resp_benchmarks.status_code == 200:
            all_benchmarks = resp_benchmarks.json()["benchmarks"]

            if all_benchmarks:
                cols = st.columns(3, gap="medium")
                for idx, benchmark in enumerate(all_benchmarks):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        benchmark_id = benchmark.get("id", "?")
                        image_hash = benchmark.get("image_hash", "")
                        hash_label = image_hash[:12] + "..." if len(image_hash) > 12 else image_hash

                        with st.container(border=True):
                            st.subheader(f"Benchmark #{benchmark_id}")

                            # Render image and mask thumbnails side by side
                            col_img, col_mask = st.columns(2)
                            with col_img:
                                img_data = benchmark.get("image", "")
                                if img_data:
                                    try:
                                        img_array = decode_array(img_data)
                                        if img_array.max() > 0:
                                            img_array = (img_array / img_array.max() * 255).astype(np.uint8)
                                        else:
                                            img_array = img_array.astype(np.uint8)
                                        pil_img = Image.fromarray(img_array, mode='L')
                                        st.image(pil_img, caption="Image", use_container_width=True)
                                    except Exception:
                                        st.caption("Image unavailable")
                                else:
                                    st.caption("No image")
                            with col_mask:
                                mask_data = benchmark.get("mask", "")
                                if mask_data:
                                    try:
                                        mask_array = decode_array(mask_data)
                                        if mask_array.max() > 0:
                                            mask_array = (mask_array / mask_array.max() * 255).astype(np.uint8)
                                        else:
                                            mask_array = mask_array.astype(np.uint8)
                                        pil_mask = Image.fromarray(mask_array, mode='L')
                                        st.image(pil_mask, caption="Mask", use_container_width=True)
                                    except Exception:
                                        st.caption("Mask unavailable")
                                else:
                                    st.caption("No mask")

                            # Hash label
                            st.caption(f"Hash {hash_label}")

                            # Action buttons
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("View Results", key=f"view_{benchmark_id}", use_container_width=True):
                                    with st.spinner("Loading results..."):
                                        resp_results = requests.get(f"{BACKEND_URL}/benchmark?id={benchmark_id}")
                                    if resp_results.status_code == 200:
                                        st.session_state.results = resp_results.json()
                                        st.session_state.show_results = True
                                        st.session_state.benchmark_id = benchmark_id
                                        st.session_state.page = "Accueil"
                                        st.rerun()
                                    else:
                                        st.error("Failed to load results")
                            with col_btn2:
                                if st.button("Run More Tests", key=f"rerun_{benchmark_id}", use_container_width=True):
                                    st.session_state.page = "Accueil"
                                    st.session_state.benchmark_exists = True
                                    st.session_state.benchmark_id = benchmark_id
                                    st.session_state.show_results = False
                                    st.rerun()

                            # Delete button
                            if st.button("Delete", key=f"delete_{benchmark_id}", use_container_width=True):
                                with st.spinner("Deleting benchmark..."):
                                    resp_delete = requests.delete(f"{BACKEND_URL}/benchmark?id={benchmark_id}")
                                if resp_delete.status_code == 200:
                                    st.rerun()
                                else:
                                    st.error("Failed to delete benchmark")
            else:
                st.info("No benchmarks in history yet. Run your first benchmark from the Home page!")
        else:
            st.error("Error loading history from backend")
    except Exception as e:
        st.error(f"Backend connection error: {str(e)}")
