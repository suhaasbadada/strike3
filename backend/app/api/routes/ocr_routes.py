import time
import io
import pytesseract
from PIL import Image
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.ocr_schema import OcrResponse, ProcessImageResponse
from app.api.routes.compression_routes import compress_text, decompress_text, verify_text
from app.schemas.compression_schema import CompressRequest, DecompressRequest, VerifyRequest

router = APIRouter(tags=["ocr"])

@router.post("/ocr", response_model=OcrResponse)
async def extract_text(file: UploadFile = File(...)):
    start = time.perf_counter()
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
        text = pytesseract.image_to_string(image).strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    latency_ms = int((time.perf_counter() - start) * 1000)
    return OcrResponse(text=text, latency=latency_ms)

@router.post("/process-image", response_model=ProcessImageResponse)
async def process_image_pipeline(file: UploadFile = File(...)):
    start_total = time.perf_counter()
    
    # 1. OCR
    ocr_start = time.perf_counter()
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
        text = pytesseract.image_to_string(image).strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    ocr_latency = int((time.perf_counter() - ocr_start) * 1000)

    if not text:
        text = "EMPTY_TEXT"
        
    # 2. Compress
    compress_req = CompressRequest(text=text)
    compress_res = compress_text(compress_req)
    
    # 3. Decompress
    decompress_req = DecompressRequest(compressed_data=compress_res.compressed_data)
    decompress_res = decompress_text(decompress_req)
    
    # 4. Verify
    verify_req = VerifyRequest(original_text=text, decompressed_text=decompress_res.text)
    verify_res = verify_text(verify_req)
    
    total_latency = int((time.perf_counter() - start_total) * 1000)
    
    return ProcessImageResponse(
        ocr_text=text,
        ocr_latency=ocr_latency,
        compression=compress_res,
        decompression=decompress_res,
        verification=verify_res,
        total_latency=total_latency
    )
