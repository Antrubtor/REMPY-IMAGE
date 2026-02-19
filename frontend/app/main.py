import streamlit as st
import requests
import json
import numpy as np
from PIL import Image
from benchmark import plot_bar, plot_scatter, plot_image
import io

st.set_page_config(page_title="REMPY-IMAGE", layout="wide")
BACKEND_URL = "http://backend:8000"

# État de navigation global
if 'page' not in st.session_state:
    st.session_state.page = "Accueil"

# Sidebar Navigation
st.sidebar.title("📱 Navigation")
if st.sidebar.button("🏠 Accueil", use_container_width=True):
    st.session_state.page = "Accueil"
    st.rerun()

if st.sidebar.button("📜 Historique", use_container_width=True):
    st.session_state.page = "Historique"
    st.rerun()

# Initialisation des états
if 'benchmark_exists' not in st.session_state:
    st.session_state.benchmark_exists = False
if 'benchmark_id' not in st.session_state:
    st.session_state.benchmark_id = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

# Page Accueil
if st.session_state.page == "Accueil":
    st.title("🔥 REMPY-IMAGE")
    st.markdown("Frontend Streamlit - Geodesic Distance Transform")
    
    st.sidebar.header("📁 Uploads")
    image_file = st.sidebar.file_uploader("Image (JPEG/PNG)", type=['jpeg', 'png'], key="image_uploader")
    mask_file = st.sidebar.file_uploader("Mask (PNG)", type=['png'], key="mask_uploader")
    nb_tests = st.sidebar.number_input("Tests", min_value=1, value=10, key="nb_tests")
    
    if image_file:
        image_bytes = image_file.getvalue()
        image = Image.open(io.BytesIO(image_bytes)).convert('L')
        image_pil = Image.open(io.BytesIO(image_file.getvalue())).convert('L')
        image_file_bytes = io.BytesIO()
        image_pil.save(image_file_bytes, format='JPEG', quality=95)
        st.sidebar.image(image, caption="Image", width=200, clamp=True)
    
    if mask_file:
        mask_bytes = mask_file.getvalue()
        st.sidebar.image(mask_bytes, caption="Mask", width=200)
    
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
                    files=files
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
                    files=files
                )
                if resp_benchmark.status_code == 200:
                    st.session_state.results = resp_benchmark.json()
                    st.session_state.show_results = True
                    st.session_state.benchmark_exists = False
                    st.rerun()
    
    # Affichage des résultats
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
                st.metric("🚀 Speedup Mean", f"{speedup_mean:.2f}x")
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

# Page Historique
elif st.session_state.page == "Historique":
    st.title("📜 Historique des Benchmarks")
    st.markdown("Toutes les combinaisons image + mask déjà utilisées")
    
    # Récupération de tous les benchmarks
    try:
        resp_benchmarks = requests.get(f"{BACKEND_URL}/benchmarks")
        if resp_benchmarks.status_code == 200:
            all_benchmarks = resp_benchmarks.json()["benchmarks"]
            
            if all_benchmarks:
                # Affichage en grille 3 colonnes
                cols = st.columns(3)
                for idx, benchmark in enumerate(all_benchmarks):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        st.markdown("---")
                        st.markdown(f"**Benchmark ID:** `{benchmark['id']}`")
                        
                        # Images
                        col_img1, col_img2 = st.columns(2)
                        with col_img1:
                            if benchmark['image_result']:
                                # Affichage de la première image résultat comme aperçu
                                img_data = benchmark['image_result'][0]
                                st.image(img_data, caption="Image", use_column_width=True)
                        with col_img2:
                            st.info("Mask associé")
                            st.caption("Disponible dans les résultats")
                        
                        # Boutons d'action
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button(f"📈 View Results\n{benchmark['id'][:8]}...", key=f"view_{benchmark['id']}"):
                                resp_results = requests.get(f"{BACKEND_URL}/benchmark?id={benchmark['id']}")
                                if resp_results.status_code == 200:
                                    st.session_state.results = resp_results.json()
                                    st.session_state.show_results = True
                                    st.session_state.benchmark_id = benchmark['id']
                                    st.session_state.page = "Accueil"  # Retour à l'accueil pour voir les résultats
                                    st.rerun()
                        
                        with col_btn2:
                            if st.button(f"🔄 New Runs\n{benchmark['id'][:8]}...", key=f"rerun_{benchmark['id']}"):
                                # Demander nb_tests pour les nouveaux runs
                                with st.expander("Configurer les nouveaux runs", expanded=False):
                                    new_nb_tests = st.number_input("Nombre de tests", min_value=1, value=10, key=f"nb_tests_{benchmark['id']}")
                                
                                if st.button(f"🚀 Lancer {new_nb_tests} runs", key=f"start_rerun_{benchmark['id']}"):
                                    # Les fichiers image/mask ne sont pas disponibles directement, mais on peut refaire avec le hash
                                    resp_benchmark = requests.post(
                                        f"{BACKEND_URL}/benchmarks/run?nb_tests={new_nb_tests}&benchmark_id={benchmark['id']}"
                                    )
                                    if resp_benchmark.status_code == 200:
                                        st.session_state.results = resp_benchmark.json()
                                        st.session_state.show_results = True
                                        st.session_state.benchmark_id = benchmark['id']
                                        st.session_state.page = "Accueil"
                                        st.rerun()
                        st.markdown("---")
            else:
                st.info("📭 Aucun benchmark dans l'historique")
        else:
            st.error("Erreur lors de la récupération de l'historique")
    except Exception as e:
        st.error(f"Erreur connexion backend: {str(e)}")
    
    # Section résultats (partagée entre les pages)
    if st.session_state.get('show_results') and st.session_state.get('results'):
        st.markdown("---")
        st.header("📊 Results")
        # Même code d'affichage des résultats que dans Accueil...
        results = st.session_state.results
        # [Code d'affichage des métriques et graphiques identique à la section précédente]
