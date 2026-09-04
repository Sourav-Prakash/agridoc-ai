/**
 * AgriDoc AI - Frontend Application Logic
 * Handles camera stream, image uploads, API interactions, and prescription rendering.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements - Tabs & Navigation
  const tabCameraBtn = document.getElementById("tab-camera-btn");
  const tabUploadBtn = document.getElementById("tab-upload-btn");
  const panelCamera = document.getElementById("panel-camera");
  const panelUpload = document.getElementById("panel-upload");

  // Elements - Camera
  const video = document.getElementById("camera-feed");
  const canvas = document.getElementById("camera-canvas");
  const cameraOverlay = document.getElementById("camera-overlay");
  const cameraPlaceholder = document.getElementById("camera-placeholder");
  const snapshotPreview = document.getElementById("camera-snapshot-preview");
  const startCameraBtn = document.getElementById("start-camera-btn");
  const switchCameraBtn = document.getElementById("switch-camera-btn");
  const captureBtn = document.getElementById("capture-btn");
  const retakeBtn = document.getElementById("retake-btn");

  // Elements - Upload
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const dropzonePrompt = document.getElementById("dropzone-prompt");
  const uploadPreviewContainer = document.getElementById("upload-preview-container");
  const uploadPreviewImg = document.getElementById("upload-preview-img");
  const uploadFileName = document.getElementById("upload-file-name");
  const removeUploadBtn = document.getElementById("remove-upload-btn");
  const diagnoseUploadBtn = document.getElementById("diagnose-upload-btn");

  // Elements - Sections
  const inputSection = document.getElementById("input-section");
  const loadingSection = document.getElementById("loading-section");
  const loadingStep = document.getElementById("loading-step");
  const errorSection = document.getElementById("error-section");
  const errorMessage = document.getElementById("error-message");
  const dismissErrorBtn = document.getElementById("dismiss-error-btn");
  const nonPlantSection = document.getElementById("non-plant-section");
  const tryAgainBtn = document.getElementById("try-again-btn");
  const resultsSection = document.getElementById("results-section");
  const newScanBtn = document.getElementById("new-scan-btn");
  const printBtn = document.getElementById("print-btn");
  const printDate = document.getElementById("print-date");

  // Elements - Settings Modal & Key Status
  const openSettingsBtn = document.getElementById("open-settings-btn");
  const bannerSetKeyBtn = document.getElementById("banner-set-key-btn");
  const closeSettingsBtn = document.getElementById("close-settings-btn");
  const cancelSettingsBtn = document.getElementById("cancel-settings-btn");
  const saveKeyBtn = document.getElementById("save-key-btn");
  const settingsModal = document.getElementById("settings-modal");
  const apiKeyInput = document.getElementById("api-key-input");
  const saveEnvCheckbox = document.getElementById("save-env-checkbox");
  const settingsStatusMsg = document.getElementById("settings-status-msg");
  const keyBadge = document.getElementById("key-badge");
  const keyBadgeText = document.getElementById("key-badge-text");
  const missingKeyBanner = document.getElementById("missing-key-banner");

  // State variables
  let currentStream = null;
  let currentFacingMode = "environment"; // default to rear camera on mobile
  let capturedBase64 = null;
  let selectedFile = null;
  let loadingInterval = null;

  // --- API Key Status & Modal ---

  async function checkKeyStatus() {
    try {
      const res = await fetch("/api/key-status");
      const data = await res.json();
      if (data.has_key) {
        keyBadge.className = "flex items-center space-x-1.5 text-xs px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
        keyBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400"></span><span>API Key Active (${data.masked_key})</span>`;
        missingKeyBanner.classList.add("hidden");
      } else {
        keyBadge.className = "flex items-center space-x-1.5 text-xs px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30";
        keyBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span><span>API Key Needed</span>`;
        missingKeyBanner.classList.remove("hidden");
      }
    } catch (e) {
      console.warn("Could not check key status:", e);
    }
  }

  function openSettings() {
    settingsStatusMsg.classList.add("hidden");
    apiKeyInput.value = "";
    settingsModal.classList.remove("hidden");
  }

  function closeSettings() {
    settingsModal.classList.add("hidden");
  }

  async function saveApiKey() {
    const key = apiKeyInput.value.trim();
    if (!key) {
      showSettingsStatus("Please enter an API key", false);
      return;
    }

    try {
      saveKeyBtn.disabled = true;
      saveKeyBtn.textContent = "Saving...";

      const res = await fetch("/api/set-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: key,
          save_to_env: saveEnvCheckbox.checked,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to save key");
      }

      showSettingsStatus("API Key updated successfully!", true);
      await checkKeyStatus();
      setTimeout(closeSettings, 900);
    } catch (err) {
      showSettingsStatus(err.message, false);
    } finally {
      saveKeyBtn.disabled = false;
      saveKeyBtn.textContent = "Save Key";
    }
  }

  function showSettingsStatus(msg, isSuccess) {
    settingsStatusMsg.textContent = msg;
    settingsStatusMsg.className = isSuccess
      ? "text-xs py-2 px-3 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200"
      : "text-xs py-2 px-3 rounded-lg bg-rose-50 text-rose-700 border border-rose-200";
    settingsStatusMsg.classList.remove("hidden");
  }

  openSettingsBtn.addEventListener("click", openSettings);
  bannerSetKeyBtn.addEventListener("click", openSettings);
  closeSettingsBtn.addEventListener("click", closeSettings);
  cancelSettingsBtn.addEventListener("click", closeSettings);
  saveKeyBtn.addEventListener("click", saveApiKey);

  // --- Tab Navigation ---

  tabCameraBtn.addEventListener("click", () => {
    tabCameraBtn.className = "flex-1 py-3.5 px-4 text-center font-medium text-sm flex items-center justify-center space-x-2 border-b-2 border-brand-600 text-brand-700 bg-white transition";
    tabUploadBtn.className = "flex-1 py-3.5 px-4 text-center font-medium text-sm flex items-center justify-center space-x-2 border-b-2 border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-100/50 transition";
    panelCamera.classList.remove("hidden");
    panelUpload.classList.add("hidden");
  });

  tabUploadBtn.addEventListener("click", () => {
    tabUploadBtn.className = "flex-1 py-3.5 px-4 text-center font-medium text-sm flex items-center justify-center space-x-2 border-b-2 border-brand-600 text-brand-700 bg-white transition";
    tabCameraBtn.className = "flex-1 py-3.5 px-4 text-center font-medium text-sm flex items-center justify-center space-x-2 border-b-2 border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-100/50 transition";
    panelUpload.classList.remove("hidden");
    panelCamera.classList.add("hidden");
    stopCamera();
  });

  // --- Camera Operations ---

  async function startCamera() {
    stopCamera();
    try {
      const constraints = {
        video: {
          facingMode: currentFacingMode,
          width: { ideal: 1280 },
          height: { ideal: 960 },
        },
        audio: false,
      };

      currentStream = await navigator.mediaDevices.getUserMedia(constraints);
      video.srcObject = currentStream;
      video.classList.remove("hidden");
      cameraOverlay.classList.remove("hidden");
      cameraPlaceholder.classList.add("hidden");
      snapshotPreview.classList.add("hidden");

      startCameraBtn.classList.add("hidden");
      switchCameraBtn.classList.remove("hidden");
      captureBtn.classList.remove("hidden");
      retakeBtn.classList.add("hidden");
    } catch (err) {
      showError(`Camera access error: ${err.message || "Could not access video device"}. You can also use the Upload Image tab.`);
    }
  }

  function stopCamera() {
    if (currentStream) {
      currentStream.getTracks().forEach((track) => track.stop());
      currentStream = null;
    }
    video.classList.add("hidden");
    cameraOverlay.classList.add("hidden");
    cameraPlaceholder.classList.remove("hidden");
    startCameraBtn.classList.remove("hidden");
    switchCameraBtn.classList.add("hidden");
    captureBtn.classList.add("hidden");
  }

  switchCameraBtn.addEventListener("click", () => {
    currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
    startCamera();
  });

  startCameraBtn.addEventListener("click", startCamera);

  captureBtn.addEventListener("click", () => {
    if (!video.videoWidth) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    capturedBase64 = canvas.toDataURL("image/jpeg", 0.92);
    snapshotPreview.src = capturedBase64;
    snapshotPreview.classList.remove("hidden");
    video.classList.add("hidden");
    cameraOverlay.classList.add("hidden");

    captureBtn.classList.add("hidden");
    switchCameraBtn.classList.add("hidden");
    retakeBtn.classList.remove("hidden");

    // Stop active camera stream while diagnosing
    if (currentStream) {
      currentStream.getTracks().forEach((track) => track.stop());
      currentStream = null;
    }

    // Trigger AI Diagnosis
    runDiagnosisBase64(capturedBase64);
  });

  retakeBtn.addEventListener("click", () => {
    capturedBase64 = null;
    snapshotPreview.classList.add("hidden");
    startCamera();
  });

  // --- File Upload & Drag-and-Drop ---

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("border-brand-500", "bg-brand-50/40");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("border-brand-500", "bg-brand-50/40");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-brand-500", "bg-brand-50/40");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleSelectedFile(e.target.files[0]);
    }
  });

  function handleSelectedFile(file) {
    if (!file.type.startsWith("image/")) {
      showError("Please select a valid image file (JPEG, PNG, WEBP)");
      return;
    }

    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      uploadPreviewImg.src = e.target.result;
      uploadFileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      dropzonePrompt.classList.add("hidden");
      uploadPreviewContainer.classList.remove("hidden");
      diagnoseUploadBtn.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
  }

  removeUploadBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = "";
    uploadPreviewImg.src = "";
    uploadPreviewContainer.classList.add("hidden");
    dropzonePrompt.classList.remove("hidden");
    diagnoseUploadBtn.classList.add("hidden");
  });

  diagnoseUploadBtn.addEventListener("click", () => {
    if (!selectedFile) return;
    runDiagnosisFile(selectedFile);
  });

  // --- Progress / Loading State ---

  const loadingSteps = [
    "Inspecting leaf foliage and surface lesions...",
    "Cross-referencing phytopathology database...",
    "Classifying pathogen genus & severity level...",
    "Formulating chemical medicines & exact dosages...",
    "Compiling organic recipes & preventive practices...",
  ];

  function startLoading() {
    hideAllAlerts();
    resultsSection.classList.add("hidden");
    loadingSection.classList.remove("hidden");

    let stepIdx = 0;
    loadingStep.textContent = loadingSteps[stepIdx];
    loadingInterval = setInterval(() => {
      stepIdx = (stepIdx + 1) % loadingSteps.length;
      loadingStep.textContent = loadingSteps[stepIdx];
    }, 2200);
  }

  function stopLoading() {
    if (loadingInterval) {
      clearInterval(loadingInterval);
      loadingInterval = null;
    }
    loadingSection.classList.add("hidden");
  }

  // --- API Diagnosis Calls ---

  async function runDiagnosisFile(file) {
    startLoading();
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/diagnose", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Diagnosis failed");
      }

      handleDiagnosisResult(data);
    } catch (err) {
      showError(err.message);
    } finally {
      stopLoading();
    }
  }

  async function runDiagnosisBase64(base64Data) {
    startLoading();
    try {
      const res = await fetch("/api/diagnose-base64", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: base64Data }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Diagnosis failed");
      }

      handleDiagnosisResult(data);
    } catch (err) {
      showError(err.message);
    } finally {
      stopLoading();
    }
  }

  // --- Handle Diagnosis Results ---

  function handleDiagnosisResult(diagnosis) {
    hideAllAlerts();

    // Check if the specimen is actually an agricultural crop/plant
    if (!diagnosis.is_plant_or_crop) {
      nonPlantSection.classList.remove("hidden");
      resultsSection.classList.add("hidden");
      nonPlantSection.scrollIntoView({ behavior: "smooth" });
      return;
    }

    // Populate Overview
    document.getElementById("res-crop-name").textContent = diagnosis.crop_name || "Unknown Crop";
    document.getElementById("res-condition-name").textContent = diagnosis.condition_name || "Condition Unspecified";
    document.getElementById("res-description").textContent = diagnosis.description_and_cause || "No description provided.";
    document.getElementById("res-confidence").textContent = `${diagnosis.confidence_score || 90}%`;

    // Badges
    const badgeType = document.getElementById("res-badge-condition-type");
    badgeType.textContent = diagnosis.condition_type || "General";

    const badgeSev = document.getElementById("res-badge-severity");
    const sev = (diagnosis.severity || "moderate").toLowerCase();
    badgeSev.textContent = `Severity: ${diagnosis.severity || "Moderate"}`;
    if (sev === "severe") {
      badgeSev.className = "text-xs font-bold px-2.5 py-1 rounded-full badge-severe";
    } else if (sev === "moderate") {
      badgeSev.className = "text-xs font-bold px-2.5 py-1 rounded-full badge-moderate";
    } else if (sev === "low") {
      badgeSev.className = "text-xs font-bold px-2.5 py-1 rounded-full badge-low";
    } else {
      badgeSev.className = "text-xs font-bold px-2.5 py-1 rounded-full badge-healthy";
    }

    const badgeUrg = document.getElementById("res-badge-urgency");
    badgeUrg.textContent = diagnosis.urgency_level || "Attention Needed";

    // Visual Symptoms
    const symptomsContainer = document.getElementById("res-symptoms-list");
    symptomsContainer.innerHTML = "";
    if (diagnosis.visual_symptoms && diagnosis.visual_symptoms.length > 0) {
      diagnosis.visual_symptoms.forEach((symptom) => {
        const pill = document.createElement("span");
        pill.className = "inline-flex items-center space-x-1.5 text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200";
        pill.innerHTML = `<i class="fa-solid fa-check text-brand-600 text-[10px]"></i><span>${escapeHtml(symptom)}</span>`;
        symptomsContainer.appendChild(pill);
      });
    } else {
      symptomsContainer.innerHTML = `<span class="text-xs text-slate-500">No acute visible lesions detected.</span>`;
    }

    // Chemical Medicines
    const chemContainer = document.getElementById("chemical-medicines-container");
    chemContainer.innerHTML = "";
    if (diagnosis.chemical_medicines && diagnosis.chemical_medicines.length > 0) {
      diagnosis.chemical_medicines.forEach((med) => {
        const card = document.createElement("div");
        card.className = "p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition";
        card.innerHTML = `
          <div class="flex items-start justify-between gap-2">
            <h4 class="font-bold text-slate-900 text-sm">${escapeHtml(med.name)}</h4>
            <span class="text-xs px-2.5 py-1 rounded-md bg-blue-100 text-blue-800 font-bold border border-blue-200 whitespace-nowrap">
              ${escapeHtml(med.dosage)}
            </span>
          </div>
          <div class="mt-1 flex flex-wrap gap-1.5 text-[11px] text-slate-600">
            <span class="bg-white px-2 py-0.5 rounded border border-slate-200"><strong>Active:</strong> ${escapeHtml(med.active_ingredient)}</span>
            <span class="bg-white px-2 py-0.5 rounded border border-slate-200"><strong>Targets:</strong> ${escapeHtml(med.target_pathogen)}</span>
          </div>
          <p class="text-xs text-slate-700 mt-2.5">
            <strong>Application:</strong> ${escapeHtml(med.application_method)}
          </p>
          <div class="mt-2.5 text-[11px] text-amber-900 bg-amber-50 px-2.5 py-1.5 rounded border border-amber-200/80 flex items-center space-x-1.5">
            <i class="fa-solid fa-clock-rotate-left text-amber-600"></i>
            <span><strong>Safety Interval (PHI):</strong> ${escapeHtml(med.waiting_period)}</span>
          </div>
        `;
        chemContainer.appendChild(card);
      });
    } else {
      chemContainer.innerHTML = `<div class="text-xs text-slate-500 italic p-3 bg-slate-50 rounded-lg">No chemical agrochemicals required for this condition.</div>`;
    }

    // Organic Remedies
    const orgContainer = document.getElementById("organic-remedies-container");
    orgContainer.innerHTML = "";
    if (diagnosis.organic_remedies && diagnosis.organic_remedies.length > 0) {
      diagnosis.organic_remedies.forEach((remedy) => {
        const card = document.createElement("div");
        card.className = "p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 hover:bg-emerald-50/60 transition";
        card.innerHTML = `
          <div class="flex items-start justify-between gap-2">
            <h4 class="font-bold text-emerald-950 text-sm">${escapeHtml(remedy.name)}</h4>
            <span class="text-[11px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium border border-emerald-300">
              Eco-Friendly
            </span>
          </div>
          <p class="text-xs text-slate-700 mt-2">
            <strong>Preparation & Dosage:</strong> ${escapeHtml(remedy.preparation_and_dosage)}
          </p>
          <p class="text-xs text-emerald-800 mt-1.5">
            <strong>Benefits:</strong> ${escapeHtml(remedy.benefits)}
          </p>
        `;
        orgContainer.appendChild(card);
      });
    } else {
      orgContainer.innerHTML = `<div class="text-xs text-slate-500 italic p-3 bg-slate-50 rounded-lg">No specific organic remedies listed.</div>`;
    }

    // Preventive Practices
    const prevList = document.getElementById("res-preventive-list");
    prevList.innerHTML = "";
    if (diagnosis.preventive_measures && diagnosis.preventive_measures.length > 0) {
      diagnosis.preventive_measures.forEach((item) => {
        const li = document.createElement("li");
        li.className = "flex items-start space-x-2";
        li.innerHTML = `<i class="fa-solid fa-circle-check text-brand-600 text-sm mt-0.5"></i><span>${escapeHtml(item)}</span>`;
        prevList.appendChild(li);
      });
    }

    // Safety & PPE Guidelines
    const safetyList = document.getElementById("res-safety-list");
    safetyList.innerHTML = "";
    if (diagnosis.safety_precautions && diagnosis.safety_precautions.length > 0) {
      diagnosis.safety_precautions.forEach((item) => {
        const li = document.createElement("li");
        li.className = "flex items-start space-x-2";
        li.innerHTML = `<i class="fa-solid fa-shield-halved text-amber-600 text-xs mt-0.5"></i><span>${escapeHtml(item)}</span>`;
        safetyList.appendChild(li);
      });
    }

    // Show results section
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  // --- Alerts & Errors ---

  function showError(msg) {
    errorMessage.textContent = msg;
    errorSection.classList.remove("hidden");
    errorSection.scrollIntoView({ behavior: "smooth" });
  }

  dismissErrorBtn.addEventListener("click", () => {
    errorSection.classList.add("hidden");
  });

  tryAgainBtn.addEventListener("click", () => {
    nonPlantSection.classList.add("hidden");
    inputSection.scrollIntoView({ behavior: "smooth" });
  });

  function hideAllAlerts() {
    errorSection.classList.add("hidden");
    nonPlantSection.classList.add("hidden");
  }

  // --- Reset / Rescan ---

  newScanBtn.addEventListener("click", () => {
    resultsSection.classList.add("hidden");
    capturedBase64 = null;
    selectedFile = null;
    fileInput.value = "";
    uploadPreviewContainer.classList.add("hidden");
    dropzonePrompt.classList.remove("hidden");
    diagnoseUploadBtn.classList.add("hidden");
    snapshotPreview.classList.add("hidden");
    retakeBtn.classList.add("hidden");
    startCameraBtn.classList.remove("hidden");
    inputSection.scrollIntoView({ behavior: "smooth" });
  });

  // --- Print Prescription Handler ---

  printBtn.addEventListener("click", () => {
    printDate.textContent = new Date().toLocaleString();
    window.print();
  });

  // Helper function to escape HTML
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initialize status on load
  checkKeyStatus();
});
