# NSphotoX

NSphotoX is an advanced image OSINT and metadata forensics toolkit built for ethical cybersecurity research, digital investigations, privacy analysis, and forensic learning.

Designed with a cyberpunk-inspired terminal interface, NSphotoX provides powerful image intelligence capabilities including EXIF metadata extraction, GPS analysis, forensic hashing, OCR analysis, AI-based exposure scoring, timeline reconstruction, anomaly detection, reverse image search integration, and interactive HTML forensic dashboards.

---

## Features

* EXIF Metadata Analysis
* GPS Intelligence & Google Maps Links
* AI Risk Analysis Engine
* OCR Text Extraction
* Face Count Detection
* Reverse Image Search Links
* MD5 / SHA1 / SHA256 Hashing
* Timeline Intelligence
* Static Anomaly Detection
* Interactive HTML Dashboard
* JSON / PDF / ZIP Report Export
* Metadata Cleaning
* Batch Investigation Mode
* Multi-format Image Support

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/NSphotoX.git
cd NSphotoX

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Optional dependencies:

```bash
brew install tesseract
```

---

## Usage

### Full forensic scan

```bash
python3 nsphotox.py scan image.jpg
```

### Generate HTML dashboard

```bash
python3 nsphotox.py html image.jpg
```

### Generate PDF report

```bash
python3 nsphotox.py pdf image.jpg
```

### Generate ZIP forensic package

```bash
python3 nsphotox.py zip image.jpg
```

### Open GPS coordinates in browser

```bash
python3 nsphotox.py gps image.jpg --open
```

### Clean metadata

```bash
python3 nsphotox.py clean image.jpg
```

### Batch folder investigation

```bash
python3 nsphotox.py batch ./photos
```

---

## Ethical Use Policy

NSphotoX is intended strictly for:

* Ethical OSINT research
* Cybersecurity learning
* Digital forensics education
* Privacy awareness
* Permission-based investigations

This project is NOT intended for:

* Stalking
* Doxxing
* Unauthorized surveillance
* Privacy violations
* Illegal investigations

Users are responsible for complying with local laws and ethical standards.

---

## Tech Stack

* Python 3
* Rich
* Pillow
* ExifRead
* OpenCV
* Pytesseract
* ReportLab

---

## Author

Developed by Naitik Soni

NSphotoX was created as a personal cybersecurity and digital forensics learning project focused on ethical image intelligence and metadata investigation workflows.

---

## Disclaimer

This toolkit is provided for educational and ethical research purposes only. The developer is not responsible for misuse, unauthorized investigations, privacy violations, or illegal activity performed using this software.

