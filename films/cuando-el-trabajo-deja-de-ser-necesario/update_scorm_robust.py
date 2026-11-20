import zipfile
import os

os.chdir(r"E:\proyectos antigrtavity\maquina de videos\films\cuando-el-trabajo-deja-de-ser-necesario")

video_name = "Cuando_El_Trabajo_Deja_De_Ser_Necesario_EducAI_Final.mp4"

# Tiempos sincronizados al final de cada sección (al terminar la voz y antes del inicio de la siguiente):
# Scene 02: Voz termina a los 110.35s -> Checkpoint a los 110.4s (01:50)
# Scene 04: Voz termina a los 228.74s -> Checkpoint a los 228.8s (03:48)
# Scene 05: Voz termina a los 286.24s -> Checkpoint a los 286.3s (04:46)
# Scene 07: Voz termina a los 404.05s -> Checkpoint a los 404.1s (06:44, justo antes del outro)

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cuando el Trabajo Deja de Ser Necesario (Interactivo)</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: 100%;
      height: 100%;
      background: #090d16;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }}
    #player-container {{
      position: relative;
      width: 100%;
      max-width: 1280px;
      aspect-ratio: 16 / 9;
      background: #000;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.7);
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    #player-container:fullscreen {{
      width: 100vw;
      height: 100vh;
      max-width: none;
      border-radius: 0;
    }}
    #player-container:-webkit-full-screen {{
      width: 100vw;
      height: 100vh;
      max-width: none;
      border-radius: 0;
    }}
    video {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }}
    #header-bar {{
      position: absolute;
      top: 14px;
      left: 18px;
      right: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 30;
      pointer-events: none;
    }}
    .status-pill {{
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #cbd5e1;
      backdrop-filter: blur(6px);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .status-pill .accent {{
      color: #38bdf8;
      font-weight: 700;
    }}
    .header-actions {{
      display: flex;
      gap: 8px;
      pointer-events: auto;
    }}
    .icon-btn {{
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.2s;
    }}
    .icon-btn:hover {{
      background: #0284c7;
      border-color: #38bdf8;
    }}

    #overlay {{
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(10, 15, 30, 0.96);
      backdrop-filter: blur(10px);
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      z-index: 100;
      animation: fadeIn 0.25s ease-out;
      overflow-y: auto;
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: scale(0.98); }} to {{ opacity: 1; transform: scale(1); }} }}
    
    .badge {{
      background: #0284c7;
      color: #ffffff;
      padding: 5px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin-bottom: 12px;
      display: inline-block;
    }}
    .question-title {{
      font-size: 20px;
      font-weight: 700;
      text-align: center;
      margin-bottom: 20px;
      max-width: 860px;
      line-height: 1.35;
      color: #f8fafc;
    }}
    .options-grid {{
      display: flex;
      flex-direction: column;
      gap: 10px;
      width: 100%;
      max-width: 820px;
    }}
    .option-btn {{
      background: #1e293b;
      border: 2px solid #334155;
      color: #f1f5f9;
      padding: 12px 18px;
      border-radius: 8px;
      font-size: 15px;
      cursor: pointer;
      text-align: left;
      line-height: 1.35;
      transition: all 0.15s ease-in-out;
    }}
    .option-btn:hover:not(:disabled) {{
      background: #334155;
      border-color: #38bdf8;
      transform: translateY(-1px);
    }}
    .option-btn.correct {{
      background: #14532d !important;
      border-color: #22c55e !important;
      color: #ffffff !important;
    }}
    .option-btn.incorrect {{
      background: #7f1d1d !important;
      border-color: #ef4444 !important;
      color: #ffffff !important;
    }}
    #feedback {{
      margin-top: 14px;
      font-size: 14px;
      font-weight: 600;
      text-align: center;
      max-width: 820px;
      line-height: 1.4;
      min-height: 24px;
    }}
    .continue-btn {{
      margin-top: 18px;
      background: #0284c7;
      color: #ffffff;
      border: none;
      padding: 10px 30px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      display: none;
      transition: background 0.2s, transform 0.15s;
    }}
    .continue-btn:hover {{
      background: #0369a1;
      transform: scale(1.02);
    }}
  </style>
</head>
<body>

<div id="player-container">
  <div id="header-bar">
    <div class="status-pill" id="next-checkpoint-info">
      <span>Próxima Pregunta:</span> <span class="accent" id="checkpoint-label">Fin de Sección 2 (en 01:50)</span>
    </div>
    <div class="header-actions">
      <div class="status-pill" id="score-pill">
        <span>Calificación:</span> <span class="accent" id="score-display">100</span>%
      </div>
      <button class="icon-btn" id="btn-fullscreen" title="Pantalla Completa">⛶ Pantalla Completa</button>
    </div>
  </div>

  <video id="video-elem" controls controlsList="nofullscreen" playsinline>
    <source src="{video_name}" type="video/mp4">
    Tu navegador no soporta video HTML5.
  </video>

  <div id="overlay">
    <div class="badge" id="section-badge">Cierre de Sección</div>
    <div class="question-title" id="q-title">Pregunta</div>
    <div class="options-grid" id="opts-container"></div>
    <div id="feedback"></div>
    <button class="continue-btn" id="btn-continue">Continuar con la clase ▶</button>
  </div>
</div>

<script>
// --- SCORM 1.2 API CONNECTOR ---
var scormAPI = null;
function findAPI(win) {{
  var attempts = 0;
  while (win && !win.API && attempts < 10) {{
    if (win.parent && win.parent !== win) win = win.parent;
    else if (win.opener) win = win.opener;
    else break;
    attempts++;
  }}
  return win ? win.API : null;
}}
function initSCORM() {{
  scormAPI = findAPI(window);
  if (scormAPI) {{
    scormAPI.LMSInitialize("");
    scormAPI.LMSSetValue("cmi.core.lesson_status", "incomplete");
    scormAPI.LMSCommit("");
  }}
}}
function finishSCORM(score) {{
  if (scormAPI) {{
    scormAPI.LMSSetValue("cmi.core.score.raw", String(Math.round(score)));
    scormAPI.LMSSetValue("cmi.core.score.min", "0");
    scormAPI.LMSSetValue("cmi.core.score.max", "100");
    var status = score >= 60 ? "passed" : "completed";
    scormAPI.LMSSetValue("cmi.core.lesson_status", status);
    scormAPI.LMSCommit("");
    scormAPI.LMSFinish("");
  }}
}}

// --- PREGUNTAS UBICADAS EXACTAMENTE AL FINAL DE CADA SECCIÓN ---
const checkpoints = [
  {{
    "scene_id": "scene_02",
    "section_title": "Sección 2: Sennett y la Flexibilidad",
    "timestamp": 110.4,
    "time_str": "01:50",
    "question": "Al concluir el análisis de Richard Sennett ('La corrosión del carácter'), ¿cuál es el impacto central de reemplazar el oficio y la estabilidad por la flexibilidad continua?",
    "options": [
      "Un incremento en la serenidad psicológica de los profesionales al rotar de trabajo frecuentemente.",
      "La imposibilidad de construir una narrativa biográfica con sentido y el desgaste del carácter al fragmentarse la trayectoria vital.",
      "La desaparición inmediata de la brecha salarial en las empresas tecnológicas.",
      "Una desaceleración en la adopción de herramientas digitales en los lugares de trabajo."
    ],
    "correct_index": 1,
    "feedback_ok": "¡Exacto! Al concluir la sección, Sennett demuestra que la estabilidad permitía tejer una historia personal continua; la flexibilidad forzada destruye esa narrativa y corroe el carácter.",
    "feedback_error": "Incorrecto. Para Sennett, el problema de fondo es existencial: al fragmentar las trayectorias vitales, se impide que la persona construya un relato coherente de su vida."
  }},
  {{
    "scene_id": "scene_04",
    "section_title": "Sección 4: Harari y la Inteligencia Ajena",
    "timestamp": 228.8,
    "time_str": "03:48",
    "question": "Al cerrar la reflexión sobre 'Nexus' de Yuval Noah Harari, ¿en qué consiste la 'alienación cognitiva' de los profesionales ante la IA?",
    "options": [
      "En perder el acceso físico a sus oficinas debido a caídas en los servidores corporativos.",
      "En tener que programar de manera artesanal los algoritmos que usan en sus tareas diarias.",
      "En retener la responsabilidad ética y legal del resultado final, mientras que el juicio y el razonamiento se delegan a un sistema opaco que no controlan.",
      "En una rebaja automática de honorarios impuesta directamente por los sistemas operativos."
    ],
    "correct_index": 2,
    "feedback_ok": "¡Respuesta brillante! El profesional queda como aval legal de decisiones que ya no comprende ni procesa íntimamente, delegando el criterio a una caja negra algorítmica.",
    "feedback_error": "Incorrecto. Harari señala que el humano sigue siendo legalmente responsable de las consecuencias, pero el proceso de pensamiento y criterio real queda en manos de la IA."
  }},
  {{
    "scene_id": "scene_05",
    "section_title": "Sección 5: La Paradoja del Capitalismo",
    "timestamp": 286.3,
    "time_str": "04:46",
    "question": "Finalizada la sección sobre automatización y RBU, ¿por qué el Ingreso Básico Universal no resuelve por sí solo la crisis de la sociedad laboral?",
    "options": [
      "Porque los bancos comerciales impiden transferencias monetarias masivas.",
      "Porque aunque asegura la subsistencia material, no restituye la estructura temporal, los lazos comunitarios ni el reconocimiento identitario que brindaba el trabajo.",
      "Porque frena la investigación en robótica e inteligencia artificial en las universidades.",
      "Porque genera inflación inmediata en todos los sectores productivos."
    ],
    "correct_index": 1,
    "feedback_ok": "¡Totalmente acertado! El RBU resuelve el piso económico y el consumo, pero el trabajo cumplía funciones comunitarias, ordenadoras y existenciales que el dinero por sí solo no suple.",
    "feedback_error": "No es correcto. El problema no es monetario: radica en que el dinero resuelve la cuenta bancaria, pero no provee identidad, rutina compartida ni reconocimiento social."
  }},
  {{
    "scene_id": "scene_07",
    "section_title": "Sección 7: Conclusión Pedagógica",
    "timestamp": 404.1,
    "time_str": "06:44",
    "question": "Como síntesis final del recorrido, ¿cuál debe ser la misión pedagógica fundamental de la educación frente al avance de la inteligencia artificial?",
    "options": [
      "Competir en memorización y rapidez técnica con las capacidades de procesamiento de los servidores.",
      "Refundarse como un espacio para el juicio ético, el pensamiento crítico, la deliberación colectiva y el cultivo de lo irreductiblemente humano.",
      "Sustituir las asignaturas humanísticas y artísticas por talleres obligatorios de programación básica.",
      "Delegar el diseño curricular y las evaluaciones a modelos predictivos sin intervención docente."
    ],
    "correct_index": 1,
    "feedback_ok": "¡Conclusión impecable! La educación no puede intentar competir con la velocidad de cómputo de la IA; su rol es cultivar el juicio crítico, la ética y la capacidad comunitaria de crear sentido.",
    "feedback_error": "Incorrecto. Frente a sistemas de procesamiento sobrehumano, la escuela no debe competir en rendimiento operario, sino refundarse en la ética, la crítica y la construcción comunitaria."
  }}
];

let triggeredTimes = new Set();
let correctAnswers = 0;
let totalQuestions = checkpoints.length;

const playerContainer = document.getElementById('player-container');
const video = document.getElementById('video-elem');
const overlay = document.getElementById('overlay');
const sectionBadge = document.getElementById('section-badge');
const qTitle = document.getElementById('q-title');
const optsContainer = document.getElementById('opts-container');
const feedback = document.getElementById('feedback');
const btnContinue = document.getElementById('btn-continue');
const scoreDisplay = document.getElementById('score-display');
const checkpointLabel = document.getElementById('checkpoint-label');
const btnFullscreen = document.getElementById('btn-fullscreen');

initSCORM();

btnFullscreen.addEventListener('click', () => {{
  if (!document.fullscreenElement && !document.webkitFullscreenElement) {{
    if (playerContainer.requestFullscreen) {{
      playerContainer.requestFullscreen();
    }} else if (playerContainer.webkitRequestFullscreen) {{
      playerContainer.webkitRequestFullscreen();
    }}
    btnFullscreen.textContent = '✕ Salir Pantalla Completa';
  }} else {{
    if (document.exitFullscreen) {{
      document.exitFullscreen();
    }} else if (document.webkitExitFullscreen) {{
      document.webkitExitFullscreen();
    }}
    btnFullscreen.textContent = '⛶ Pantalla Completa';
  }}
}});

video.addEventListener('timeupdate', () => {{
  const curT = video.currentTime;
  
  let nextCpIdx = checkpoints.findIndex((cp, idx) => !triggeredTimes.has(idx));
  if (nextCpIdx !== -1) {{
    checkpointLabel.textContent = `${{checkpoints[nextCpIdx].section_title}} (en ${{checkpoints[nextCpIdx].time_str}})`;
  }} else {{
    checkpointLabel.textContent = 'Todas las secciones completadas';
  }}

  checkpoints.forEach((cp, idx) => {{
    if (!triggeredTimes.has(idx) && curT >= cp.timestamp && curT <= cp.timestamp + 1.2) {{
      triggeredTimes.add(idx);
      triggerCheckpoint(cp);
    }}
  }});
}});

video.addEventListener('ended', () => {{
  const finalScore = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 100;
  finishSCORM(finalScore);
}});

function triggerCheckpoint(cp) {{
  video.pause();
  overlay.style.display = 'flex';
  sectionBadge.textContent = cp.section_title || 'Cierre de Sección';
  qTitle.textContent = cp.question;
  feedback.textContent = '';
  btnContinue.style.display = 'none';
  optsContainer.innerHTML = '';

  cp.options.forEach((optText, i) => {{
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.textContent = optText;
    btn.onclick = () => selectOption(btn, i, cp);
    optsContainer.appendChild(btn);
  }});
}}

function selectOption(selectedBtn, chosenIdx, cp) {{
  const allBtns = optsContainer.querySelectorAll('.option-btn');
  allBtns.forEach(b => b.disabled = true);

  if (chosenIdx === cp.correct_index) {{
    selectedBtn.classList.add('correct');
    feedback.textContent = cp.feedback_ok || "¡Respuesta Correcta!";
    feedback.style.color = '#4ade80';
    correctAnswers++;
  }} else {{
    selectedBtn.classList.add('incorrect');
    feedback.textContent = cp.feedback_error || "Respuesta incorrecta.";
    feedback.style.color = '#f87171';
    allBtns[cp.correct_index].classList.add('correct');
  }}

  const scorePct = totalQuestions > 0 ? Math.round((correctAnswers / totalQuestions) * 100) : 100;
  scoreDisplay.textContent = scorePct;
  if (scormAPI) {{
    scormAPI.LMSSetValue("cmi.core.score.raw", String(scorePct));
    scormAPI.LMSCommit("");
  }}
  btnContinue.style.display = 'inline-block';
}}

btnContinue.onclick = () => {{
  overlay.style.display = 'none';
  video.play();
}};
</script>
</body>
</html>
"""

manifest_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="educai_scorm_cuando_el_trabajo_deja_d" version="1.2"
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
      <title>Cuando el Trabajo Deja de Ser Necesario (Interactivo)</title>
      <item identifier="item_01" identifierref="res_01">
        <title>Cuando el Trabajo Deja de Ser Necesario (Interactivo)</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res_01" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
      <file href="{video_name}"/>
    </resource>
  </resources>
</manifest>
"""

# Reempaquetar SCORM Completo
zip_full = 'Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM_Completo.zip'
print("Empaquetando nuevo SCORM Completo sincronizado a fin de sección...")
with zipfile.ZipFile(zip_full, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', html_content.encode('utf-8'))
    z.writestr('imsmanifest.xml', manifest_content.encode('utf-8'))
    z.write(video_name, arcname=video_name)

size_mb = os.path.getsize(zip_full) / (1024 * 1024)
print(f"SCORM Completo creado: {size_mb:.2f} MB")

# Reempaquetar SCORM Liviano (Zero-Weight)
zip_light = 'Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM.zip'
with zipfile.ZipFile(zip_light, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', html_content.encode('utf-8'))
    z.writestr('imsmanifest.xml', manifest_content.replace(f'<file href="{video_name}"/>', '').encode('utf-8'))

print("SCORM Liviano actualizado exitosamente.")
