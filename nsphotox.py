#!/usr/bin/env python3
import argparse, os, hashlib, csv, json, time, webbrowser, zipfile, math
from datetime import datetime
from PIL import Image
import exifread
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

console = Console()

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

try:
    import cv2
except Exception:
    cv2 = None

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None

BANNER = r"""
███╗   ██╗███████╗██████╗ ██╗  ██╗ ██████╗ ████████╗ ██████╗ ██╗  ██╗
████╗  ██║██╔════╝██╔══██╗██║  ██║██╔═══██╗╚══██╔══╝██╔═══██╗╚██╗██╔╝
██╔██╗ ██║███████╗██████╔╝███████║██║   ██║   ██║   ██║   ██║ ╚███╔╝
██║╚██╗██║╚════██║██╔═══╝ ██╔══██║██║   ██║   ██║   ██║   ██║ ██╔██╗
██║ ╚████║███████║██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██╔╝ ██╗
╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝

        NSphotoX v4 :: CYBER IMAGE OSINT + FORENSICS SUITE
        Author: Naitik Soni | Ethical Investigation Mode
"""

def banner():
    console.print(f"[bold green]{BANNER}[/bold green]")
    console.print("[yellow]Use only on your own images, public images, or permission-based cases.[/yellow]\n")

def boot():
    steps = ["Booting forensic core", "Loading metadata parser", "Checking GPS traces",
             "Running anomaly scan", "Building cyber report"]
    with Progress(SpinnerColumn(), TextColumn("[green]{task.description}"), BarColumn()) as p:
        t = p.add_task("Starting", total=len(steps))
        for s in steps:
            p.update(t, description=s)
            time.sleep(0.18)
            p.advance(t)

def h(path, algo):
    x = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            x.update(chunk)
    return x.hexdigest()

def tags(path):
    with open(path, "rb") as f:
        return exifread.process_file(f, details=True)

def dms(vals, ref):
    d = float(vals[0].num) / vals[0].den
    m = float(vals[1].num) / vals[1].den
    s = float(vals[2].num) / vals[2].den
    dec = d + m / 60 + s / 3600
    return -dec if ref in ["S", "W"] else dec

def gps_from(t):
    lat, latr = t.get("GPS GPSLatitude"), t.get("GPS GPSLatitudeRef")
    lon, lonr = t.get("GPS GPSLongitude"), t.get("GPS GPSLongitudeRef")
    if lat and latr and lon and lonr:
        return dms(lat.values, str(latr)), dms(lon.values, str(lonr))
    return None, None

def entropy(path):
    data = open(path, "rb").read()
    if not data: return 0
    freq = [0] * 256
    for b in data: freq[b] += 1
    return -sum((c/len(data)) * math.log2(c/len(data)) for c in freq if c)

def strings_extract(path):
    data = open(path, "rb").read()
    out, cur = [], ""
    for b in data:
        if 32 <= b <= 126: cur += chr(b)
        else:
            if len(cur) >= 6: out.append(cur)
            cur = ""
    return out

def ai_risk(t, lat, lon, path):
    score, notes = 0, []
    if lat and lon:
        score += 40; notes.append("GPS location metadata exposed")
    if "Image Model" in t or "Image Make" in t:
        score += 20; notes.append("Device/camera model exposed")
    if "EXIF DateTimeOriginal" in t:
        score += 20; notes.append("Original capture timestamp exposed")
    if "Image Software" in t:
        score += 10; notes.append("Software/editing trace found")
    if entropy(path) > 7.9:
        score += 10; notes.append("High entropy: possible compressed/embedded data")
    level = "LOW" if score < 30 else "MEDIUM" if score < 70 else "HIGH"
    return min(score, 100), level, notes

def vision(path):
    result = {"faces_count": "opencv-not-installed", "ocr_text": "", "objects": []}
    if cv2:
        try:
            img = cv2.imread(path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = cascade.detectMultiScale(gray, 1.1, 5)
            result["faces_count"] = len(faces)
        except Exception:
            result["faces_count"] = "error"
    if pytesseract:
        try:
            result["ocr_text"] = pytesseract.image_to_string(Image.open(path))[:2000]
        except Exception:
            result["ocr_text"] = ""
    return result

def reverse_links(path):
    name = os.path.basename(path)
    return {
        "Google Images": "https://images.google.com/",
        "Yandex Images": "https://yandex.com/images/",
        "TinEye": "https://tineye.com/",
        "Note": f"Upload this image manually: {name}"
    }

def anomaly(path):
    data = open(path, "rb").read()
    s = strings_extract(path)
    flags = []
    if b"<script" in data.lower(): flags.append("Script-like content found")
    if b"<?php" in data.lower(): flags.append("PHP-like content found")
    if b"MZ" in data[:2048]: flags.append("Executable header pattern near start")
    if len(s) > 500: flags.append("Large amount of embedded readable strings")
    if entropy(path) > 7.9: flags.append("Very high entropy")
    return flags or ["No obvious suspicious static pattern found"]

def timeline(t, path):
    return {
        "Captured": str(t.get("EXIF DateTimeOriginal", "Unknown")),
        "Modified EXIF": str(t.get("Image DateTime", "Unknown")),
        "File Modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
        "File Accessed": datetime.fromtimestamp(os.path.getatime(path)).isoformat()
    }

def collect(path):
    t = tags(path)
    lat, lon = gps_from(t)
    score, level, notes = ai_risk(t, lat, lon, path)
    img = Image.open(path)
    return {
        "tool": "NSphotoX v4",
        "author": "Naitik Soni",
        "file": path,
        "name": os.path.basename(path),
        "size": os.path.getsize(path),
        "format": img.format,
        "resolution": f"{img.size[0]}x{img.size[1]}",
        "hashes": {"md5": h(path,"md5"), "sha1": h(path,"sha1"), "sha256": h(path,"sha256")},
        "gps": {"lat": lat, "lon": lon, "maps": f"https://maps.google.com/?q={lat},{lon}" if lat and lon else None},
        "risk": {"score": score, "level": level, "notes": notes},
        "timeline": timeline(t, path),
        "vision": vision(path),
        "reverse_search": reverse_links(path),
        "anomaly": anomaly(path),
        "metadata": {str(k): str(v) for k,v in t.items()}
    }

def scan(path):
    banner(); boot()
    r = collect(path)
    console.print(Panel.fit(f"[cyan]TARGET[/cyan]\n{path}", title="NSphotoX Console", border_style="green"))

    ft = Table(title="File Intelligence", box=box.DOUBLE_EDGE)
    ft.add_column("Field", style="cyan"); ft.add_column("Value")
    for k in ["name","size","format","resolution"]:
        ft.add_row(k, str(r[k]))
    ft.add_row("MD5", r["hashes"]["md5"])
    ft.add_row("SHA256", r["hashes"]["sha256"])
    console.print(ft)

    if r["gps"]["maps"]:
        console.print(Panel(f"Latitude: {r['gps']['lat']}\nLongitude: {r['gps']['lon']}\nMaps: {r['gps']['maps']}", title="Geo Intelligence", border_style="green"))

    risk_color = "green" if r["risk"]["level"]=="LOW" else "yellow" if r["risk"]["level"]=="MEDIUM" else "red"
    console.print(Panel(f"{r['risk']['level']} RISK — {r['risk']['score']}/100\n" + "\n".join("• "+x for x in r["risk"]["notes"]), title="AI Risk Engine", border_style=risk_color))

    console.print(Panel("\n".join(f"{k}: {v}" for k,v in r["timeline"].items()), title="Timeline Intelligence"))
    console.print(Panel(f"Faces Count: {r['vision']['faces_count']}\nOCR Preview:\n{r['vision']['ocr_text'][:500] or 'No OCR text found'}", title="Local Vision / OCR"))
    console.print(Panel("\n".join("• "+x for x in r["anomaly"]), title="Static Anomaly Scan"))

def html(path):
    os.makedirs("output", exist_ok=True)
    r = collect(path)
    out = "output/nsphotox_v4_dashboard.html"
    html = f"""<!DOCTYPE html>
<html><head><title>NSphotoX v4 Report</title>
<style>
body{{background:#030712;color:#00ff99;font-family:monospace;padding:30px}}
.card{{border:1px solid #00ff99;border-radius:16px;padding:18px;margin:18px 0;box-shadow:0 0 25px #00ff9955;background:#07111f}}
h1,h2{{color:#38ffbd}} a{{color:#7dd3fc}} .danger{{color:#ff4d6d}} .ok{{color:#00ff99}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
pre{{white-space:pre-wrap;color:#d1fae5}}
button{{background:#00ff99;color:#001;border:0;padding:10px 14px;border-radius:10px;font-weight:bold}}
</style></head><body>
<h1>⚡ NSphotoX v4 Cyber Forensic Dashboard</h1>
<div class="grid">
<div class="card"><h2>File</h2><p>{r['name']}</p><p>{r['format']} | {r['resolution']}</p></div>
<div class="card"><h2>Risk</h2><p class="danger">{r['risk']['level']} — {r['risk']['score']}/100</p></div>
<div class="card"><h2>GPS</h2><p>{r['gps']['maps'] or 'No GPS found'}</p></div>
</div>
<div class="card"><h2>Reverse Image Search</h2>
<a href="https://images.google.com/" target="_blank"><button>Google Images</button></a>
<a href="https://yandex.com/images/" target="_blank"><button>Yandex</button></a>
<a href="https://tineye.com/" target="_blank"><button>TinEye</button></a>
</div>
<div class="card"><h2>Timeline</h2><pre>{json.dumps(r['timeline'], indent=2)}</pre></div>
<div class="card"><h2>Vision / OCR</h2><pre>{json.dumps(r['vision'], indent=2)}</pre></div>
<div class="card"><h2>Anomaly Scan</h2><pre>{json.dumps(r['anomaly'], indent=2)}</pre></div>
<div class="card"><h2>Metadata</h2><pre>{json.dumps(r['metadata'], indent=2)}</pre></div>
</body></html>"""
    open(out, "w").write(html)
    console.print(f"[green]HTML dashboard saved:[/green] {out}")

def json_report(path):
    os.makedirs("output", exist_ok=True)
    out = "output/nsphotox_v4_report.json"
    json.dump(collect(path), open(out,"w"), indent=2)
    console.print(f"[green]JSON saved:[/green] {out}")

def pdf(path):
    if not canvas:
        console.print("[red]reportlab not installed[/red]"); return
    os.makedirs("output", exist_ok=True)
    r = collect(path)
    out = "output/nsphotox_v4_report.pdf"
    c = canvas.Canvas(out, pagesize=letter)
    text = c.beginText(40, 740)
    text.textLine("NSphotoX v4 Forensic Report")
    text.textLine(f"File: {r['name']}")
    text.textLine(f"Risk: {r['risk']['level']} {r['risk']['score']}/100")
    text.textLine(f"Maps: {r['gps']['maps']}")
    text.textLine(f"MD5: {r['hashes']['md5']}")
    text.textLine(f"SHA256: {r['hashes']['sha256'][:60]}...")
    text.textLine("Timeline:")
    for k,v in r["timeline"].items(): text.textLine(f"  {k}: {v}")
    c.drawText(text); c.save()
    console.print(f"[green]PDF saved:[/green] {out}")

def clean(path):
    os.makedirs("output", exist_ok=True)
    img = Image.open(path)
    out = "output/clean_" + os.path.basename(path)
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))
    clean_img.save(out)
    console.print(f"[green]Clean image saved:[/green] {out}")

def zip_report(path):
    html(path); json_report(path); pdf(path)
    out = "output/nsphotox_case_package.zip"
    with zipfile.ZipFile(out, "w") as z:
        for f in ["output/nsphotox_v4_dashboard.html","output/nsphotox_v4_report.json","output/nsphotox_v4_report.pdf"]:
            if os.path.exists(f): z.write(f)
    console.print(f"[green]ZIP case package saved:[/green] {out}")

def gps(path, open_map):
    r = collect(path)
    link = r["gps"]["maps"]
    print(link or "No GPS metadata found")
    if open_map and link: webbrowser.open(link)

def batch(folder):
    os.makedirs("output", exist_ok=True)
    out = "output/batch_report.csv"
    rows = []
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            try:
                r = collect(p)
                rows.append({"file":name,"format":r["format"],"risk":r["risk"]["level"],"score":r["risk"]["score"],"maps":r["gps"]["maps"] or "","sha256":r["hashes"]["sha256"]})
            except Exception:
                pass
    with open(out,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file","format","risk","score","maps","sha256"])
        w.writeheader(); w.writerows(rows)
    console.print(f"[green]Batch CSV saved:[/green] {out}")

def main():
    p = argparse.ArgumentParser(description="NSphotoX v4")
    s = p.add_subparsers(dest="cmd")
    for cmd in ["scan","html","json","pdf","zip","clean"]:
        x=s.add_parser(cmd); x.add_argument("image")
    g=s.add_parser("gps"); g.add_argument("image"); g.add_argument("--open", action="store_true")
    b=s.add_parser("batch"); b.add_argument("folder")
    a=p.parse_args()
    if a.cmd=="scan": scan(a.image)
    elif a.cmd=="html": html(a.image)
    elif a.cmd=="json": json_report(a.image)
    elif a.cmd=="pdf": pdf(a.image)
    elif a.cmd=="zip": zip_report(a.image)
    elif a.cmd=="clean": clean(a.image)
    elif a.cmd=="gps": gps(a.image, a.open)
    elif a.cmd=="batch": batch(a.folder)
    else: banner(); p.print_help()

if __name__ == "__main__":
    main()
