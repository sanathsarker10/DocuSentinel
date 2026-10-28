# DocuSentinel

A beginner-friendly SIH prototype for screening uploaded documents for suspicious indicators. It is not a definitive forgery detector.

## Features
- Upload PDF, JPG, or PNG files (up to 10 MB)
- Extract text from PDFs and images using OCR
- Display basic PDF/image metadata
- Run simple image-quality checks
- Create a supporting Error Level Analysis (ELA) visualization
- Generate a downloadable PDF report

## Requirements
- Python 3.10 or newer
- Tesseract OCR installed on your computer
- VS Code

## Run locally in VS Code

### 1. Install Tesseract OCR
- **Windows:** Install Tesseract OCR and note its installation path. If Python cannot find it, add the Tesseract folder to your Windows PATH, then restart VS Code.
- **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
- **macOS with Homebrew:** `brew install tesseract`

### 2. Open the project folder
Extract the ZIP, then open the `DocuSentinel` folder in VS Code.

### 3. Create a virtual environment
In the VS Code terminal:

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

### 4. Install Python dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the app
```bash
streamlit run app.py
```

Streamlit will show a local URL, usually `http://localhost:8501`.

## Deploy online using Streamlit Community Cloud
1. Create a GitHub repository and upload all project files.
2. Open Streamlit Community Cloud at https://share.streamlit.io/
3. Sign in with GitHub and choose **Create app**.
4. Select your repository, branch, and `app.py`.
5. Deploy. `requirements.txt` installs Python packages and `packages.txt` requests the Tesseract system package on supported Streamlit build images.
6. Test the deployed app with sample documents.

Deployment behavior and system-package support can change. If the build fails, review the deployment logs and use the current Streamlit Community Cloud documentation.

## Important limitations
- Metadata dates do not prove that a PDF was altered.
- ELA is not a reliable standalone forgery detector. Resaving, scanning, or recompressing a legitimate image can create visual differences.
- The current prototype does not authenticate an issuer, validate a government registry, or reliably verify every PDF digital signature.
- The current image checks are basic quality/screening checks, not a trained tampering classifier.
- Do not upload real personal documents to a public demo. Use synthetic or consented test documents and review the hosting provider's privacy/retention policies.

