import zipfile
import os

os.chdir(r"E:\proyectos antigrtavity\maquina de videos\films\cuando-el-trabajo-deja-de-ser-necesario")

old_zip = 'Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM.zip'
with zipfile.ZipFile(old_zip, 'r') as z:
    html_content = z.read('index.html').decode('utf-8')
    manifest_content = z.read('imsmanifest.xml').decode('utf-8')

video_name = 'Cuando_El_Trabajo_Deja_De_Ser_Necesario_EducAI_Final.mp4'

# Corregir el nombre del video en el tag <source>
html_fixed = html_content.replace('Cuando_El_Trabajo_Deja_De_Ser_Necesario_Final.mp4', video_name)

# Incluir el archivo mp4 en el manifest
manifest_fixed = manifest_content.replace(
    '<file href="index.html"/>',
    f'<file href="index.html"/>\n      <file href="{video_name}"/>'
)

# 1. Actualizar el paquete liviano (Zero-Weight con referencia exacta corregida)
with zipfile.ZipFile('Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM.zip', 'w', zipfile.ZIP_DEFLATED) as z_light:
    z_light.writestr('index.html', html_fixed.encode('utf-8'))
    z_light.writestr('imsmanifest.xml', manifest_content.encode('utf-8'))
print("Paquete liviano corregido: Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM.zip")

# 2. Generar el paquete autocontenido con el video MP4 integrado adentro
autocontenido_zip = 'Cuando_El_Trabajo_Deja_De_Ser_Necesario_SCORM_Completo.zip'
print("Creando paquete SCORM autocontenido con video incluido...")
with zipfile.ZipFile(autocontenido_zip, 'w', zipfile.ZIP_DEFLATED) as z_full:
    z_full.writestr('index.html', html_fixed.encode('utf-8'))
    z_full.writestr('imsmanifest.xml', manifest_fixed.encode('utf-8'))
    z_full.write(video_name, arcname=video_name)

size_mb = os.path.getsize(autocontenido_zip) / (1024 * 1024)
print(f"Paquete completo generado exitosamente: {size_mb:.2f} MB")
