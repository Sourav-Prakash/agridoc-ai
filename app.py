import os
import json
import base64
import io
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image

from google import genai
from google.genai import types

# Load environment variables from .env file
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

app = FastAPI(title="AgriDoc AI - Crop Disease Diagnosis & Remedy Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global runtime API key state
runtime_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "").strip() or None


def get_active_api_key() -> Optional[str]:
    """Retrieve active API key from runtime memory or environment."""
    global runtime_api_key
    if runtime_api_key:
        return runtime_api_key
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        runtime_api_key = env_key
        return env_key
    return None


# --- Pydantic Data Models for Structured Diagnosis Output ---

class ChemicalMedicine(BaseModel):
    name: str = Field(description="Commercial and generic agrochemical name, e.g. Mancozeb 75% WP, Chlorothalonil 720 SC")
    active_ingredient: str = Field(description="Primary active chemical compound, e.g. Mancozeb, Copper Oxychloride, Imidacloprid")
    target_pathogen: str = Field(description="Target pathogen or pest, e.g. Alternaria solani spores, Aphids, Downy mildew")
    dosage: str = Field(description="Exact dosage and dilution ratio, e.g. 2.0 to 2.5 g per liter of clean water")
    application_method: str = Field(description="Instructions on application: foliar spray, coverage, timing (e.g. spray early morning or late evening)")
    waiting_period: str = Field(description="Pre-harvest interval (PHI), e.g. 'Wait at least 7 days after application before harvesting'")


class OrganicRemedy(BaseModel):
    name: str = Field(description="Name of the organic/biological solution, e.g. Cold-Pressed Neem Oil (10,000 PPM), Trichoderma viride, Baking Soda spray")
    preparation_and_dosage: str = Field(description="Preparation formulation, dilution ratio, and application steps")
    benefits: str = Field(description="Eco-friendly benefits, soil health impact, and resistance prevention")


class CropDiagnosis(BaseModel):
    is_plant_or_crop: bool = Field(description="True if the image contains a plant, crop, leaf, stem, fruit, or vegetable; False if non-agricultural image")
    crop_name: str = Field(description="Common name and botanical name of the plant, e.g. Tomato (Solanum lycopersicum)")
    condition_name: str = Field(description="Name of the diagnosed condition, disease, pest infestation, nutrient deficiency, or 'Healthy Plant'")
    condition_type: str = Field(description="Category: Fungal, Bacterial, Viral, Pest Infestation, Nutrient Deficiency, Environmental Stress, or Healthy")
    severity: str = Field(description="Severity rating: None, Low, Moderate, Severe")
    confidence_score: int = Field(description="Diagnostic confidence percentage between 1 and 100")
    urgency_level: str = Field(description="Immediate Action Needed, Moderate Attention, or Routine Maintenance")
    visual_symptoms: List[str] = Field(description="Key visible symptoms detected on foliage, fruit, stem, or veins")
    description_and_cause: str = Field(description="Clear scientific summary of the disease, pathogen cause, and environmental triggers like humidity or rainfall")
    chemical_medicines: List[ChemicalMedicine] = Field(description="List of conventional chemical agrochemicals with precise dosages. Empty if healthy.")
    organic_remedies: List[OrganicRemedy] = Field(description="List of organic, botanical, and biological remedies. Empty if healthy.")
    preventive_measures: List[str] = Field(description="Actionable cultural and agronomic preventative practices (e.g. drip irrigation, crop rotation, sanitizing pruning shears)")
    safety_precautions: List[str] = Field(description="Protective gear (PPE), spraying precautions, wind conditions, and pollinator/bee safety advice")


class KeyUpdateRequest(BaseModel):
    api_key: str
    save_to_env: bool = True


class Base64DiagnoseRequest(BaseModel):
    image_base64: str


# --- Routes ---

@app.get("/api/key-status")
def key_status():
    """Check if an active Gemini API key is configured."""
    key = get_active_api_key()
    if not key:
        return {"has_key": False, "masked_key": None}
    
    masked = key[:4] + "..." + key[-4:] if len(key) >= 8 else "****"
    return {"has_key": True, "masked_key": masked}


@app.post("/api/set-key")
def set_key(req: KeyUpdateRequest):
    """Set or update the active Gemini API key."""
    global runtime_api_key
    new_key = req.api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty")

    runtime_api_key = new_key

    if req.save_to_env:
        try:
            lines = []
            key_found = False
            if ENV_PATH.exists():
                with open(ENV_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            lines.append(f"GEMINI_API_KEY={new_key}\n")
                            key_found = True
                        else:
                            lines.append(line)
            if not key_found:
                lines.append(f"GEMINI_API_KEY={new_key}\n")
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            # Key still active in memory even if writing file fails
            print(f"Warning: could not write to .env: {e}")

    masked = new_key[:4] + "..." + new_key[-4:] if len(new_key) >= 8 else "****"
    return {"success": True, "message": "API key successfully updated", "masked_key": masked}


SYSTEM_PROMPT = """You are an expert Senior Plant Pathologist and Agricultural Extension Specialist with decades of field agronomy experience.
Your mission is to examine images of crops, plants, vegetables, and fruits, identify any diseases, pests, fungal infections, bacterial blights, viral syndromes, or nutrient deficiencies, and prescribe accurate, safe, and actionable treatment recommendations.

Guidelines:
1. Carefully inspect the leaf surface, veins, stem, discoloration, lesions, spots, haloing, rust pustules, or wilting.
2. If the image is NOT a plant or crop specimen (e.g. an animal, car, unrelated object), set `is_plant_or_crop` to false.
3. If the plant is completely healthy, set `condition_name` to "Healthy Crop", `condition_type` to "Healthy", `severity` to "None", and leave medicine lists empty.
4. For diseased/infected crops:
   - Provide accurate common commercial and generic names for chemical medicines (e.g. Mancozeb, Copper Oxychloride, Chlorothalonil, Azoxystrobin, Imidacloprid, Streptocycline).
   - Specify EXACT dosage formulas (e.g. "2 to 2.5 grams per liter of water" or "1.5 to 2 ml per liter").
   - State the Pre-Harvest Interval (PHI) / waiting period clearly for chemical applications to ensure food safety.
   - Prescribe high-quality organic remedies (e.g. cold-pressed neem oil 10,000 ppm, Trichoderma, Pseudomonas fluorescens, potassium bicarbonate).
   - Provide preventive agronomic practices (irrigation management, pruning of infected lower canopy, crop rotation, soil drainage).
   - Detail safety gear (gloves, eye protection, respirator/mask) and environmental safety (spraying during calm weather to prevent bee exposure).
"""


def process_image_and_diagnose(image_bytes: bytes, mime_type: str = "image/jpeg") -> CropDiagnosis:
    """Analyze crop image using Gemini multimodal vision with structured Pydantic schema."""
    api_key = get_active_api_key()
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Gemini API Key is missing. Please configure your API key in settings or .env file."
        )

    # Validate image using Pillow
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img.verify()
        # Reset stream and convert if needed
        pil_img = Image.open(io.BytesIO(image_bytes))
        # Normalize format to JPEG or PNG
        buffer = io.BytesIO()
        if pil_img.format in ["JPEG", "JPG"]:
            pil_img.save(buffer, format="JPEG", quality=90)
            clean_mime = "image/jpeg"
        else:
            pil_img.save(buffer, format="PNG")
            clean_mime = "image/png"
        clean_bytes = buffer.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    try:
        client = genai.Client(api_key=api_key)
        
        models_to_try = [
            os.getenv("GEMINI_MODEL", "").strip(),
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-pro",
        ]
        models_to_try = [m for m in models_to_try if m]

        response = None
        last_err = None

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(
                            data=clean_bytes,
                            mime_type=clean_mime,
                        ),
                        "Carefully diagnose this crop specimen. Identify the crop, identify the disease/condition, assess severity and symptoms, and provide a full dual prescription of chemical medicines (with exact dosages) and organic remedies.",
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=CropDiagnosis,
                        temperature=0.2,
                    ),
                )
                if response and response.text:
                    break
            except Exception as m_err:
                last_err = m_err
                err_upper = str(m_err).upper()
                retryable_tokens = [
                    "404", "NOT_FOUND", "NOT AVAILABLE", "NO LONGER AVAILABLE",
                    "503", "UNAVAILABLE", "HIGH DEMAND", "OVERLOADED", 
                    "RESOURCE_EXHAUSTED", "429", "RATE_LIMIT", "DEADLINE_EXCEEDED"
                ]
                if any(token in err_upper for token in retryable_tokens):
                    continue
                raise m_err

        if not response or not response.text:
            raise last_err or RuntimeError("No response from diagnostic model")

        raw_json = response.text
        diagnosis_data = json.loads(raw_json)
        return CropDiagnosis(**diagnosis_data)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "403" in error_msg or "API key not valid" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="The provided Gemini API key is invalid. Please verify your key at https://aistudio.google.com/"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Diagnostic analysis failed: {error_msg}"
        )


@app.post("/api/diagnose", response_model=CropDiagnosis)
async def diagnose_file(file: UploadFile = File(...)):
    """Diagnose crop disease from uploaded multipart file."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG, WEBP, etc.)")
    
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 20MB limit")
    
    return process_image_and_diagnose(contents, file.content_type)


@app.post("/api/diagnose-base64", response_model=CropDiagnosis)
def diagnose_base64(req: Base64DiagnoseRequest):
    """Diagnose crop disease from base64 data URI (captured from live camera)."""
    raw_str = req.image_base64
    if "," in raw_str:
        header, b64data = raw_str.split(",", 1)
        mime = "image/jpeg"
        if "image/png" in header:
            mime = "image/png"
        elif "image/webp" in header:
            mime = "image/webp"
    else:
        b64data = raw_str
        mime = "image/jpeg"

    try:
        image_bytes = base64.b64decode(b64data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    return process_image_and_diagnose(image_bytes, mime)


# --- Static Files & Frontend Routing ---
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "AgriDoc AI Backend Running. Static index.html not yet deployed."})


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host=host, port=port, reload=True)
