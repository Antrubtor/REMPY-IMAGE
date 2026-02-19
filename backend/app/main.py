import io, time, hashlib

import numpy as np

from database import create_table, save_benchmark, get_benchmark, get_all_benchmarks, get_benchmark_id_with_hash_db, delete_benchmark, delete_all_benchmarks
from geodesic_distance import propagation, npropagation
from imageio.v3 import imread
from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI(title="REMPY-IMAGE API")

create_table()


@app.post("/benchmarks/run")
async def run_benchmark(nb_tests: int,
                    image: UploadFile = File(...),
                    mask: UploadFile = File()):
    """
    Run nb_tests benchmark avec l'image et le masque
    Si ces images et masque n'avaient pas été utilisées avant une ligne est rajouté dans la DB dans benchmarks
    Sinon seulement des lignes sont rajoutées dans benchmarks_times pour les nouveaux benchmarks
    """
    if image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail=f"Uploadez seulement des images")

    image_content = await image.read()
    mask_content = await mask.read()

    combined_hash = hashlib.sha256(image_content + mask_content).hexdigest()    # hash des images pour éviter de faire plusieurs fois les benchmarks

    image_data = imread(io.BytesIO(image_content))
    mask_data = imread(io.BytesIO(mask_content))
    results = {"benchmarks": []}
    for i in range(nb_tests):
        start_time = time.time()
        p = propagation(image_data, mask_data)
        end_time = time.time()

        if i == 0:
            results["image_result"] = p.tolist()

        nstart_time = time.time()
        npropagation(image_data, mask_data)
        nend_time = time.time()

        results["benchmarks"].append({
            "python_time": end_time - start_time,
            "numba_time": nend_time - nstart_time
        })

    if not save_benchmark(combined_hash, image_data.tolist(), mask_data.tolist(), results):
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du benchmark")

    results["image_result"] = np.array([]).tolist() ##TODO remove
    results["image"] = np.array([]).tolist() ##TODO remove
    results["mask"] = np.array([]).tolist() ##TODO remove
    return results

@app.post("/benchmark/hash")
async def get_benchmark_id_with_hash(image: UploadFile = File(...),
                            mask: UploadFile = File()):
    """
    Récupère l'id du benchmark correspondant à l'image et au masque dans la DB
    """
    if image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail=f"Uploadez seulement des images")

    image_content = await image.read()
    mask_content = await mask.read()

    combined_hash = hashlib.sha256(image_content + mask_content).hexdigest()    # hash des images pour éviter de faire plusieurs fois les benchmarks

    existing = get_benchmark_id_with_hash_db(combined_hash)
    if existing:
        return { "benchmark_id": existing }
    else:
        raise HTTPException(status_code=404, detail="Aucun benchmark trouvé pour ces images")

@app.get("/benchmark")
async def get_benchmark_id(id: int):
    """
    Récupère le benchmark correspondant à l'id dans la DB
    """
    benchmark = get_benchmark(id)
    if benchmark is None:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du benchmark")
    benchmark["image_result"] = np.array([]).tolist() ##TODO remove
    benchmark["image"] = np.array([]).tolist() ##TODO remove
    benchmark["mask"] = np.array([]).tolist() ##TODO remove
    return benchmark

@app.get("/benchmarks")
async def get_benchmarks():
    """
    Récupère tous les benchmarks de la DB
    """
    benchmarks = get_all_benchmarks()
    if benchmarks is None:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des benchmarks")
    for benchmark in benchmarks["benchmarks"]:    ##TODO remove
        benchmark["image_result"] = np.array([]).tolist() ##TODO remove
        benchmark["image"] = np.array([]).tolist() ##TODO remove
        benchmark["mask"] = np.array([]).tolist() ##TODO remove
    return benchmarks

@app.delete("/benchmark")
async def delete_benchmark_id(id: int):
    """
    Supprime le benchmark correspondant à l'id dans la DB
    """
    status = delete_benchmark(id)
    return { "deleted": status }

@app.delete("/benchmarks")
async def delete_benchmarks():
    """S
    upprime tous les benchmarks de la DB
    """
    status =  delete_all_benchmarks()
    return { "deleted": status }