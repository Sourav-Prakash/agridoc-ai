```python
"""
AgriDoc AI - Streamlit Web Application
Ready for Streamlit Community Cloud deployment.
"""

import os
import json
import io
from typing import List, Optional
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st
from PIL import Image
from pydantic import BaseModel, Field

from google import genai
from google.genai import types


# ============================================================
# ENVIRONMENT
# ============================================================

# Load local .env if present.
# On Streamlit Cloud, use Settings -> Secrets instead.
ENV_PATH = Path(__file__).resolve().parent / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AgriDoc AI - Crop Disease Diagnosis & Remedy Advisor",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 800;
            color: #065f46;
            margin-bottom: 0.2rem;
        }

        .sub-header {
            font-size: 1.05rem;
            color: #4b5563;
            margin-bottom: 1.5rem;
        }

        .severity-severe {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.85rem;
            border: 1px solid #f87171;
        }

        .severity-moderate {
            background-color: #fef3c7;
            color: #92400e;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.85rem;
            border: 1px solid #fcd34d;
        }

        .severity-low {
            background-color: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.85rem;
            border: 1px solid #93c5fd;
        }

        .med-card {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
        }

        .dosage-badge {
            background-color: #dbeafe;
            color: #1e40af;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.8rem;
        }

        .phi-badge {
            background-color: #fef3c7;
            color: #92400e;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            margin-top: 6px;
            display: inline-block;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class ChemicalMedicine(BaseModel):
    name: str = Field(
        description="Commercial and generic agrochemical name"
    )
    active_ingredient: str = Field(
        description="Primary active chemical compound"
    )
    target_pathogen: str = Field(
        description="Target pathogen or pest"
    )
    dosage: str = Field(
        description="Exact dosage and dilution ratio per liter"
    )
    application_method: str = Field(
        description="Application guidelines: foliar spray, timing, etc."
    )
    waiting_period: str = Field(
        description="Pre-harvest interval before consumption"
    )


class OrganicRemedy(BaseModel):
    name: str = Field(
        description="Name of the organic or biological remedy"
    )
    preparation_and_dosage: str = Field(
        description="Preparation recipe, dilution ratio, and application steps"
    )
    benefits: str = Field(
        description="Eco-friendly benefits and plant health impact"
    )


class CropDiagnosis(BaseModel):
    is_plant_or_crop: bool = Field(
        description="True if image contains plant foliage or crop specimen"
    )
    crop_name: str = Field(
        description="Common and botanical plant name"
    )
    condition_name: str = Field(
        description="Diagnosed condition or Healthy Plant"
    )
    condition_type: str = Field(
        description="Fungal, Bacterial, Viral, Pest Infestation, Nutrient Deficiency, or Healthy"
    )
    severity: str = Field(
        description="None, Low, Moderate, Severe"
    )
    confidence_score: int = Field(
        description="Confidence percentage 1-100"
    )
    urgency_level: str = Field(
        description="Immediate Action Needed, Moderate Attention, or Routine Maintenance"
    )
    visual_symptoms: List[str] = Field(
        description="Key visible symptoms observed"
    )
    description_and_cause: str = Field(
        description="Scientific summary of disease, cause, and triggers"
    )
    chemical_medicines: List[ChemicalMedicine] = Field(
        description="Chemical agrochemicals with exact dosages"
    )
    organic_remedies: List[OrganicRemedy] = Field(
        description="Organic and biological remedies"
    )
    preventive_measures: List[str] = Field(
        description="Agronomic cultural practices"
    )
    safety_precautions: List[str] = Field(
        description="PPE and spraying safety precautions"
    )


# ============================================================
# AI SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an expert Senior Plant Pathologist and Agricultural Extension
Specialist with decades of field agronomy experience.

Your mission is to examine images of crops, plants, vegetables, and fruits,
identify diseases, pests, fungal infections, bacterial blights, viral
syndromes, or nutrient deficiencies, and provide accurate, safe, and
actionable treatment recommendations.

Guidelines:

1. Carefully inspect the leaf surface, veins, stem, discoloration, lesions,
   spots, haloing, rust pustules, or wilting.

2. If the image is NOT a plant or crop specimen, set
   `is_plant_or_crop` to false.

3. For diseased crops, provide relevant commercial and generic agrochemicals,
   appropriate dosage information, pre-harvest safety intervals (PHI),
   natural organic remedies, and preventive measures.

4. Do not fabricate certainty. If visual evidence is insufficient, clearly
   communicate uncertainty.

5. Treatment recommendations should be considered informational and should
   be verified against local agricultural regulations and product labels.
"""


# ============================================================
# API KEY
# ============================================================

def get_api_key() -> Optional[str]:
    """
    Get the Gemini API key.

    Priority:
    1. Streamlit Cloud Secrets
    2. Local environment variable / .env

    Users are NOT asked to provide their own API key.
    """

    # Streamlit Cloud Secrets
    try:
        if "GEMINI_API_KEY" in st.secrets:
            secret_key = str(st.secrets["GEMINI_API_KEY"]).strip()

            if secret_key:
                return secret_key
    except Exception:
        pass

    # Local development (.env / environment variable)
    env_key = os.getenv("GEMINI_API_KEY", "").strip()

    if env_key:
        return env_key

    return None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.image(
        "https://cdn-icons-png.flaticon.com/512/628/628283.png",
        width=64
    )

    st.title("AgriDoc AI")
    st.caption("AI Crop Pathologist & Prescription Advisor")

    st.divider()

    active_key = get_api_key()

    if active_key:
        masked = (
            active_key[:4] + "..." + active_key[-4:]
            if len(active_key) >= 8
            else "****"
        )

        st.success(f"AI Diagnosis Ready ({masked})")

    else:
        st.error("AI service is temporarily unavailable.")

    st.divider()

    st.markdown(
        """
        **How to use:**

        1. Capture a leaf using your camera or upload an image.
        2. Click **Run Diagnosis**.
        3. Review the diagnosis, treatment information,
           organic remedies, and prevention advice.
        """
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="main-header">🌾 AgriDoc AI: Crop Disease Identifier</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-header">'
    'Instant AI plant pathology diagnosis with chemical treatment information, '
    'organic remedies, and safety guidance.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# IMAGE INPUT
# ============================================================

tab_camera, tab_upload = st.tabs(
    ["📸 Live Camera", "📁 Upload Image"]
)

image_bytes = None


with tab_camera:

    camera_pic = st.camera_input(
        "Take a picture of the diseased crop leaf"
    )

    if camera_pic is not None:
        image_bytes = camera_pic.getvalue()


with tab_upload:

    uploaded_file = st.file_uploader(
        "Choose a crop photo (JPEG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file is not None:

        image_bytes = uploaded_file.getvalue()

        st.image(
            image_bytes,
            caption="Uploaded Image",
            width=350
        )


# ============================================================
# DIAGNOSIS FUNCTION
# ============================================================

def diagnose_crop(
    img_data: bytes,
    api_key: str
) -> CropDiagnosis:

    # Normalize image using Pillow
    pil_img = Image.open(io.BytesIO(img_data))

    buffer = io.BytesIO()

    if pil_img.format in ["JPEG", "JPG"]:

        pil_img.save(
            buffer,
            format="JPEG",
            quality=90
        )

        clean_mime = "image/jpeg"

    else:

        pil_img.save(
            buffer,
            format="PNG"
        )

        clean_mime = "image/png"

    clean_bytes = buffer.getvalue()

    # Gemini client
    client = genai.Client(
        api_key=api_key
    )

    # Try models in order
    models_to_try = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-pro",
    ]

    response = None
    last_err = None

    for model_name in models_to_try:

        try:

            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(
                        data=clean_bytes,
                        mime_type=clean_mime
                    ),
                    (
                        "Carefully diagnose this crop specimen. "
                        "Identify the crop, identify the disease or condition, "
                        "assess severity and symptoms, and provide treatment "
                        "information including chemical medicines, appropriate "
                        "dosages, organic remedies, prevention, and safety advice."
                    ),
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

        except Exception as e:

            last_err = e
            err_up = str(e).upper()

            retryable_errors = [
                "404",
                "NOT_FOUND",
                "503",
                "UNAVAILABLE",
                "HIGH DEMAND",
                "RESOURCE_EXHAUSTED",
                "429",
            ]

            if any(error in err_up for error in retryable_errors):
                continue

            raise e

    if not response or not response.text:

        raise (
            last_err
            or RuntimeError("Diagnostic models unavailable")
        )

    return CropDiagnosis(
        **json.loads(response.text)
    )


# ============================================================
# RUN DIAGNOSIS
# ============================================================

if image_bytes is not None:

    if st.button(
        "🔬 Diagnose Crop Health",
        type="primary",
        use_container_width=True
    ):

        api_key = get_api_key()

        if not api_key:

            st.error(
                "AI diagnosis is temporarily unavailable. "
                "Please try again later."
            )

        else:

            with st.spinner(
                "Analyzing foliage and formulating diagnosis..."
            ):

                try:

                    result = diagnose_crop(
                        image_bytes,
                        api_key
                    )

                    # ------------------------------------------------
                    # NON-PLANT IMAGE
                    # ------------------------------------------------

                    if not result.is_plant_or_crop:

                        st.warning(
                            "The provided image does not appear to be "
                            "an agricultural plant or leaf. Please capture "
                            "a clear photo of the crop."
                        )

                    else:

                        st.success(
                            "Diagnosis Complete!"
                        )

                        # ------------------------------------------------
                        # OVERVIEW
                        # ------------------------------------------------

                        st.markdown(
                            f"### {result.crop_name}"
                        )

                        st.markdown(
                            f"**Diagnosed Condition:** "
                            f"{result.condition_name}"
                        )

                        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

                        with col_m1:
                            st.metric(
                                "Pathogen Type",
                                result.condition_type
                            )

                        with col_m2:
                            st.metric(
                                "Severity",
                                result.severity
                            )

                        with col_m3:
                            st.metric(
                                "Diagnostic Confidence",
                                f"{result.confidence_score}%"
                            )

                        with col_m4:
                            st.metric(
                                "Urgency",
                                result.urgency_level
                            )

                        st.info(
                            f"**Pathology Summary:** "
                            f"{result.description_and_cause}"
                        )

                        # ------------------------------------------------
                        # SYMPTOMS
                        # ------------------------------------------------

                        if result.visual_symptoms:

                            st.markdown(
                                "**Detected Visual Symptoms:**"
                            )

                            for symptom in result.visual_symptoms:
                                st.markdown(
                                    f"- {symptom}"
                                )

                        st.divider()

                        # ------------------------------------------------
                        # TREATMENTS
                        # ------------------------------------------------

                        col_chem, col_org = st.columns(2)

                        # Chemical treatment
                        with col_chem:

                            st.markdown(
                                "#### 💊 Chemical Agrochemicals & Dosages"
                            )

                            if result.chemical_medicines:

                                for med in result.chemical_medicines:

                                    st.markdown(
                                        f"""
                                        <div class="med-card">
                                            <strong>{med.name}</strong><br>
                                            <span class="dosage-badge">
                                                Dosage: {med.dosage}
                                            </span><br>
                                            <small>
                                                <strong>Active Ingredient:</strong>
                                                {med.active_ingredient}
                                            </small><br>
                                            <small>
                                                <strong>Targets:</strong>
                                                {med.target_pathogen}
                                            </small><br>
                                            <small>
                                                <strong>Application:</strong>
                                                {med.application_method}
                                            </small><br>
                                            <div class="phi-badge">
                                                ⚠️ Safety Waiting Period (PHI):
                                                {med.waiting_period}
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                            else:

                                st.write(
                                    "No chemical treatment required."
                                )

                        # Organic treatment
                        with col_org:

                            st.markdown(
                                "#### 🌿 Organic & Biological Remedies"
                            )

                            if result.organic_remedies:

                                for org in result.organic_remedies:

                                    st.markdown(
                                        f"""
                                        <div class="med-card"
                                             style="
                                             border-color:#a7f3d0;
                                             background-color:#f0fdf4;
                                             ">
                                            <strong style="color:#065f46;">
                                                {org.name}
                                            </strong><br>

                                            <small>
                                                <strong>
                                                    Preparation & Dosage:
                                                </strong>
                                                {org.preparation_and_dosage}
                                            </small><br>

                                            <small style="color:#047857;">
                                                <strong>
                                                    Benefits:
                                                </strong>
                                                {org.benefits}
                                            </small>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                            else:

                                st.write(
                                    "No specific organic remedies needed."
                                )

                        st.divider()

                        # ------------------------------------------------
                        # PREVENTION & SAFETY
                        # ------------------------------------------------

                        col_prev, col_safe = st.columns(2)

                        with col_prev:

                            st.markdown(
                                "#### 🛡️ Agronomic Prevention Practices"
                            )

                            for prevention in result.preventive_measures:

                                st.markdown(
                                    f"✅ {prevention}"
                                )

                        with col_safe:

                            st.markdown(
                                "#### ⚠️ Spraying Safety & PPE"
                            )

                            for safety in result.safety_precautions:

                                st.markdown(
                                    f"🥽 {safety}"
                                )

                except Exception as ex:

                    st.error(
                        f"Diagnostic Error: {str(ex)}"
                    )
```
