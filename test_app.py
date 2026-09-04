"""
Verification and self-test suite for AgriDoc AI.
Tests Pydantic schemas, route definitions, and mock response validation.
"""

import json
from app import CropDiagnosis, ChemicalMedicine, OrganicRemedy, app

def test_schema_validation():
    sample_data = {
        "is_plant_or_crop": True,
        "crop_name": "Tomato (Solanum lycopersicum)",
        "condition_name": "Early Blight (Alternaria solani)",
        "condition_type": "Fungal",
        "severity": "Severe",
        "confidence_score": 94,
        "urgency_level": "Immediate Action Needed",
        "visual_symptoms": [
            "Concentric dark brown rings on lower leaves",
            "Yellow halo around circular lesions",
            "Premature defoliation of bottom foliage"
        ],
        "description_and_cause": "Early blight is caused by the fungal pathogen Alternaria solani, thriving in humid, warm conditions.",
        "chemical_medicines": [
            {
                "name": "Mancozeb 75% WP",
                "active_ingredient": "Mancozeb",
                "target_pathogen": "Alternaria solani spores",
                "dosage": "2.0 - 2.5 g per liter of water",
                "application_method": "Foliar spray on both leaf sides every 7-10 days",
                "waiting_period": "Wait 7 days before harvest (PHI: 7 days)"
            }
        ],
        "organic_remedies": [
            {
                "name": "Cold-Pressed Neem Oil Spray (10,000 PPM)",
                "preparation_and_dosage": "Dilute 5 ml neem oil with 2 ml liquid soap per liter of water",
                "benefits": "Bio-fungicidal action without harming beneficial insects"
            }
        ],
        "preventive_measures": [
            "Prune infected lower foliage 12 inches above the soil line",
            "Switch to drip irrigation to avoid wet foliage",
            "Implement a 3-year nightshade crop rotation"
        ],
        "safety_precautions": [
            "Wear chemical-resistant gloves, goggles, and respirator mask when spraying",
            "Do not spray near open waterways or during active bee foraging hours"
        ]
    }

    diagnosis = CropDiagnosis(**sample_data)
    assert diagnosis.is_plant_or_crop is True
    assert diagnosis.crop_name.startswith("Tomato")
    assert len(diagnosis.chemical_medicines) == 1
    assert diagnosis.chemical_medicines[0].active_ingredient == "Mancozeb"
    assert len(diagnosis.organic_remedies) == 1
    print("Schema validation test: PASSED")

def test_route_registry():
    routes = [route.path for route in app.routes]
    expected = [
        "/api/key-status",
        "/api/set-key",
        "/api/diagnose",
        "/api/diagnose-base64",
        "/",
        "/static"
    ]
    for exp in expected:
        assert any(exp in r for r in routes), f"Route {exp} missing"
    print("Route registry test: PASSED")

if __name__ == "__main__":
    print("Running AgriDoc AI diagnostic tests...")
    test_schema_validation()
    test_route_registry()
    print("All core tests passed successfully!")
