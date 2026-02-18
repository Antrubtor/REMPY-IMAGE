import io, time, hashlib
from database import create_table, get_benchmark_if_exist, save_benchmark, get_all_benchmarks, delete_all_benchmarks
from geodesic_distance import propagation
from imageio.v3 import imread
from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI(title="REMPY-IMAGE API")

create_table()


@app.post("/benchmark")
async def benchmark(image: UploadFile = File(...),
                    mask: UploadFile = File()):
    if image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail=f"Uploadez seulement des images")

    image_content = await image.read()
    mask_content = await mask.read()

    combined_hash = hashlib.sha256(image_content + mask_content).hexdigest()    # hash des images pour éviter de faire plusieurs fois les benchmarks

    existing = get_benchmark_if_exist(combined_hash)
    if existing:
        return {"execution_time": existing["time"] }

    image_data = imread(io.BytesIO(image_content))
    mask_data = imread(io.BytesIO(mask_content))

    start_time = time.time()
    propagation(image_data, mask_data)
    execution_time = time.time() - start_time

    if not save_benchmark(combined_hash, execution_time):
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du benchmark")
    return { "execution_time": execution_time }


@app.get("/benchmarks")
async def list_benchmarks():
    benchmarks = get_all_benchmarks()
    if benchmarks is None:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des benchmarks")
    return benchmarks

@app.delete("/benchmark")
async def delete_benchmarks():
    status =  delete_all_benchmarks()
    return { "deleted": status }