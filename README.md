# Memoria
## 1. Ejecutar con Python

### Clonar repo
`git clone https://github.com/aledzs/GDBFrontendMemoria.git`

`cd GDBFrontendMemoria`

### Crear ambiente virtual (opcional)

`python -m venv <nombre>`

`source <nombre>/bin/activate`

### Instalar requisitos

`pip install -r requirements.txt`

### Ejecutar el programa

`python main.py <binario>`

## 2. Generar ejecutable con PyInstaller

`pyinstaller -F --onefile main.py`

`chmod +x dist/main`

`dist/main <binario>`