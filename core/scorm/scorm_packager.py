"""
Interactive SCORM 1.2 Video Shell Generator (Zero-Weight Architecture).
Builds a lightweight SCORM 1.2 compliant .zip package (< 500 KB) that plays
video via external stream or local file, pauses at target timestamps, displays
trivia checkpoints, and reports scores directly to Moodle gradebook.
"""

import os
import sys
import json
import zipfile
import argparse

SCORM_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0f172a;
      color: #f8fafc;
      font-family: 'Segoe UI', system-ui, sans-serif;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    #player-container {
      position: relative;
      width: 100%;
      max-width: 1280px;
      aspect-ratio: 16 / 9;
      background: #000000;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      border-radius: 12px;
      overflow: hidden;
    }
    video {
      width: 100%;
      height: 100%;
      display: block;
    }
    #overlay {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(8px);
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px;
      z-index: 50;
      animation: fadeIn 0.3s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .badge {
      background: #0284c7;
      color: #ffffff;
      padding: 6px 16px;
      border-radius: 9999px;
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 16px;
    }
    .question-title {
      font-size: 26px;
      font-weight: 700;
      text-align: center;
      margin-bottom: 24px;
      max-width: 800px;
      line-height: 1.3;
    }
    .options-grid {
      display: flex;
      flex-direction: column;
      gap: 12px;
      width: 100%;
      max-width: 700px;
    }
    .option-btn {
      background: #1e293b;
      border: 2px solid #334155;
      color: #f1f5f9;
      padding: 14px 20px;
      border-radius: 10px;
      font-size: 18px;
      cursor: pointer;
      text-align: left;
      transition: all 0.2s;
    }
    .option-btn:hover {
      background: #334155;
      border-color: #38bdf8;
    }
    .option-btn.correct {
      background: #166534;
      border-color: #22c55e;
      color: #ffffff;
    }
    .option-btn.incorrect {
      background: #991b1b;
      border-color: #ef4444;
      color: #ffffff;
    }
    #feedback {
      margin-top: 20px;
      font-size: 18px;
      font-weight: 600;
      text-align: center;
      min-height: 28px;
    }
    .continue-btn {
      margin-top: 24px;
      background: #0284c7;
      color: #ffffff;
      border: none;
      padding: 12px 36px;
      border-radius: 8px;
      font-size: 18px;
      font-weight: 700;
      cursor: pointer;
      display: none;
      transition: background 0.2s;
    }
    .continue-btn:hover { background: #0369a1; }
    #score-bar {
      position: absolute;
      top: 20px;
      right: 24px;
      background: rgba(30, 41, 59, 0.85);
      border: 1px solid #475569;
      padding: 8px 18px;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 600;
      z-index: 20;
    }
  </style>
</head>
<body>

<div id="player-container">
  <div id="score-bar">Calificación: <span id="score-display">100</span>%</div>
  <video id="video-elem" controls playsinline>
    <source src="{video_url}" type="video/mp4">
    Tu navegador no soporta video HTML5.
  </video>

  <div id="overlay">
    <div class="badge">Trivia Interactiva Formativa</div>
    <div class="question-title" id="q-title">Pregunta</div>
    <div class="options-grid" id="opts-container"></div>
    <div id="feedback"></div>
    <button class="continue-btn" id="btn-continue">Continuar con la clase ▶</button>
  </div>
</div>

<script>
// --- SCORM 1.2 API WRAPPER ---
var scormAPI = null;
function findAPI(win) {
  var attempts = 0;
  while (win && !win.API && attempts < 10) {
    if (win.parent && win.parent !== win) win = win.parent;
    else if (win.opener) win = win.opener;
    else break;
    attempts++;
  }
  return win ? win.API : null;
}
function initSCORM() {
  scormAPI = findAPI(window);
  if (scormAPI) {
    scormAPI.LMSInitialize("");
    scormAPI.LMSSetValue("cmi.core.lesson_status", "incomplete");
    scormAPI.LMSCommit("");
  }
}
function finishSCORM(score) {
  if (scormAPI) {
    scormAPI.LMSSetValue("cmi.core.score.raw", String(Math.round(score)));
    scormAPI.LMSSetValue("cmi.core.score.min", "0");
    scormAPI.LMSSetValue("cmi.core.score.max", "100");
    var status = score >= 60 ? "passed" : "completed";
    scormAPI.LMSSetValue("cmi.core.lesson_status", status);
    scormAPI.LMSCommit("");
    scormAPI.LMSFinish("");
  }
}

// --- INTERACTIVE TIMELINE DATA ---
const checkpoints = {checkpoints_json};
let currentCheckpointIdx = 0;
let triggeredTimes = new Set();
let correctAnswers = 0;
let totalQuestions = checkpoints.length;

const video = document.getElementById('video-elem');
const overlay = document.getElementById('overlay');
const qTitle = document.getElementById('q-title');
const optsContainer = document.getElementById('opts-container');
const feedback = document.getElementById('feedback');
const btnContinue = document.getElementById('btn-continue');
const scoreDisplay = document.getElementById('score-display');

initSCORM();

video.addEventListener('timeupdate', () => {
  const curT = video.currentTime;
  checkpoints.forEach((cp, idx) => {
    if (!triggeredTimes.has(idx) && Math.abs(curT - cp.timestamp) < 0.6) {
      triggeredTimes.add(idx);
      triggerCheckpoint(cp);
    }
  });
});

video.addEventListener('ended', () => {
  const finalScore = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 100;
  finishSCORM(finalScore);
});

function triggerCheckpoint(cp) {
  video.pause();
  overlay.style.display = 'flex';
  qTitle.textContent = cp.question;
  feedback.textContent = '';
  btnContinue.style.display = 'none';
  optsContainer.innerHTML = '';

  cp.options.forEach((optText, i) => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.textContent = optText;
    btn.onclick = () => selectOption(btn, i, cp);
    optsContainer.appendChild(btn);
  });
}

function selectOption(selectedBtn, chosenIdx, cp) {
  const allBtns = optsContainer.querySelectorAll('.option-btn');
  allBtns.forEach(b => b.disabled = true);

  if (chosenIdx === cp.correct_index) {
    selectedBtn.classList.add('correct');
    feedback.textContent = cp.feedback_ok || "¡Respuesta Correcta!";
    feedback.style.color = '#4ade80';
    correctAnswers++;
  } else {
    selectedBtn.classList.add('incorrect');
    feedback.textContent = cp.feedback_error || "Respuesta incorrecta.";
    feedback.style.color = '#f87171';
    allBtns[cp.correct_index].classList.add('correct');
  }

  const scorePct = totalQuestions > 0 ? Math.round((correctAnswers / totalQuestions) * 100) : 100;
  scoreDisplay.textContent = scorePct;
  if (scormAPI) {
    scormAPI.LMSSetValue("cmi.core.score.raw", String(scorePct));
    scormAPI.LMSCommit("");
  }
  btnContinue.style.display = 'block';
}

btnContinue.onclick = () => {
  overlay.style.display = 'none';
  video.play();
};
</script>
</body>
</html>
"""

MANIFEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{identifier}" version="1.2"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
                              http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org_default">
    <organization identifier="org_default">
      <title>{title}</title>
      <item identifier="item_01" identifierref="res_01">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res_01" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>
"""

def build_scorm_package(title, video_url, checkpoints, output_zip):
    import re
    identifier = "educai_scorm_" + re.sub(r'[^a-zA-Z0-9_]', '_', title.lower())[:24]

    html_content = SCORM_HTML_TEMPLATE.replace("{title}", title) \
                                      .replace("{video_url}", video_url) \
                                      .replace("{checkpoints_json}", json.dumps(checkpoints, ensure_ascii=False))

    manifest_content = MANIFEST_XML.replace("{identifier}", identifier) \
                                   .replace("{title}", title)

    # Build zip in memory/disk
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
      zf.writestr("index.html", html_content)
      zf.writestr("imsmanifest.xml", manifest_content)

    size_kb = os.path.getsize(output_zip) / 1024
    print(f"[OK] Paquete SCORM 1.2 creado exitosamente: {output_zip} ({size_kb:.1f} KB)")
    return output_zip

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de paquete SCORM 1.2 interactivo ultra-liviano.")
    parser.add_argument("--title", required=True, help="Título del curso/lección")
    parser.add_argument("--video-url", required=True, help="URL de streaming del video MP4 (externo o relativo)")
    parser.add_argument("--checkpoints-json", required=True, help="Ruta al archivo JSON con las preguntas y timestamps")
    parser.add_argument("--output", "-o", default="paquete_scorm.zip", help="Archivo .zip de salida")
    args = parser.parse_args()

    with open(args.checkpoints_json, "r", encoding="utf-8") as f:
        cps = json.load(f)

    build_scorm_package(args.title, args.video_url, cps, args.output)
