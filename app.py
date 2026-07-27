import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from PIL import Image
from werkzeug.utils import secure_filename

from devices import get_device, get_device_list
from geolocations import get_city, get_city_list


def _refresh_windows_path():
    """Обновляет PATH из реестра Windows, чтобы найти свежие установки (например, ExifTool)."""
    if sys.platform != "win32":
        return
    try:
        import winreg
        machine = winreg.QueryValueEx(
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            "Path",
        )[0]
        user = winreg.QueryValueEx(
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment"),
            "Path",
        )[0]
        os.environ["PATH"] = f"{machine};{user};{os.environ.get('PATH', '')}"
    except Exception:
        pass


_refresh_windows_path()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"
THUMBNAIL_DIR = BASE_DIR / "static" / "thumbnails"

ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "tiff", "tif", "webp", "heic", "heif",
    "mp4", "mov", "m4v", "avi", "mkv", "webm", "3gp",
}

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "tif", "webp", "heic", "heif"}
VIDEO_EXTENSIONS = {"mp4", "mov", "m4v", "avi", "mkv", "webm", "3gp"}

UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)
THUMBNAIL_DIR.mkdir(exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def exiftool_path():
    return shutil.which("exiftool") or shutil.which("exiftool.exe")


def exiftool_ok():
    return exiftool_path() is not None


def run_exiftool(args, timeout=120):
    tool = exiftool_path()
    if not tool:
        raise RuntimeError("ExifTool не найден. Установите ExifTool и добавьте его в PATH.")

    cmd = [tool, "-charset", "UTF8", "-ignoreMinorErrors"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0 and "Warning" not in result.stderr and "1 image files updated" not in result.stdout:
        if "Overwriting" not in result.stdout:
            raise RuntimeError(f"ExifTool error: {result.stderr or result.stdout}")
    return result


def read_file_metadata(filepath):
    tool = exiftool_path()
    if not tool:
        return {"error": "ExifTool not found"}

    cmd = [tool, "-json", "-a", str(filepath)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return {"error": result.stderr}

    try:
        data = json.loads(result.stdout)
        return data[0] if data else {}
    except json.JSONDecodeError:
        return {"error": "Failed to parse ExifTool output"}


def make_thumbnail(src_path, thumb_path, size=(300, 300)):
    try:
        with Image.open(src_path) as img:
            img.thumbnail(size)
            img.save(thumb_path, "JPEG", quality=85)
        return True
    except Exception:
        return False


def is_image(ext):
    return ext.lower() in IMAGE_EXTENSIONS


def is_video(ext):
    return ext.lower() in VIDEO_EXTENSIONS


def _apply_gps_tags(tags, location, ext):
    if not location:
        return
    lat = location["lat"]
    lon = location["lon"]
    alt = location.get("alt", 0)

    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"
    alt_ref = "Above Sea Level" if alt >= 0 else "Below Sea Level"

    tags += [
        f"-GPSLatitude={lat}",
        f"-GPSLongitude={lon}",
        f"-GPSAltitude={abs(alt)}",
        f"-GPSLatitudeRef={lat_ref}",
        f"-GPSLongitudeRef={lon_ref}",
        f"-GPSAltitudeRef={alt_ref}",
    ]

    tags += ["-GPSVersionID=2.2.0.0"]
    if not is_image(ext):
        if location.get("city"):
            iso6709 = f"{lat:+.4f}{lon:+.4f}{alt:+.3f}/"
            tags += [f"-UserData:Location={iso6709}"]


def _set_file_dates_from_exif(filepath):
    metadata = read_file_metadata(filepath)
    date_str = metadata.get("DateTimeOriginal") or metadata.get("CreateDate") or metadata.get("ModifyDate")
    if not date_str:
        return
    try:
        clean = date_str.split("+")[0].split("-")[0].strip()
        dt = datetime.strptime(clean, "%Y:%m:%d %H:%M:%S")
        timestamp = dt.timestamp()
        os.utime(filepath, (timestamp, timestamp))
    except Exception:
        pass


if sys.platform == "win32":
    def _set_windows_creation_time(filepath, timestamp):
        try:
            import ctypes
            from ctypes import wintypes

            FILE_WRITE_ATTRIBUTES = 0x0100
            OPEN_EXISTING = 3

            filepath = os.path.abspath(filepath)
            handle = ctypes.windll.kernel32.CreateFileW(
                filepath, FILE_WRITE_ATTRIBUTES, 0, None, OPEN_EXISTING, 0, None
            )
            if handle == -1:
                return

            ctime = wintypes.FILETIME()
            atime = wintypes.FILETIME()
            mtime = wintypes.FILETIME()

            epoch = datetime(1970, 1, 1)
            dt = datetime.fromtimestamp(timestamp)
            intervals = int((dt - epoch).total_seconds() * 10_000_000)
            intervals += 11644473600 * 10_000_000  # Windows epoch offset

            ctime.dwLowDateTime = intervals & 0xFFFFFFFF
            ctime.dwHighDateTime = intervals >> 32
            atime.dwLowDateTime = ctime.dwLowDateTime
            atime.dwHighDateTime = ctime.dwHighDateTime
            mtime.dwLowDateTime = ctime.dwLowDateTime
            mtime.dwHighDateTime = ctime.dwHighDateTime

            ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ctime), ctypes.byref(atime), ctypes.byref(mtime))
            ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass

    def set_file_dates(filepath, timestamp):
        _set_file_dates_from_exif(filepath)
        _set_windows_creation_time(filepath, timestamp)
else:
    def set_file_dates(filepath, timestamp):
        _set_file_dates_from_exif(filepath)


def apply_metadata(src_path, dst_path, device, ip_address=None, preserve_dates=True, location=None):
    shutil.copy2(src_path, dst_path)

    original_metadata = read_file_metadata(src_path) if preserve_dates else {}
    original_date = original_metadata.get("DateTimeOriginal") or original_metadata.get("CreateDate")
    capture_date = original_date or datetime.now().strftime("%Y:%m:%d %H:%M:%S")

    ext = dst_path.suffix.lower().lstrip(".")
    tags = []

    if is_image(ext):
        tags += [
            "-XMP:All=",
            "-IPTC:All=",
            "-MakerNotes:All=",
            "-EXIF:HostComputer=",
            f"-EXIF:Make={device['make']}",
            f"-EXIF:Model={device['model']}",
            f"-EXIF:LensModel={device['lens_model']}",
            f"-EXIF:Software={device['software']}",
            "-ColorSpace=sRGB",
            "-XResolution=72",
            "-YResolution=72",
            "-ResolutionUnit=inches",
            f"-DateTimeOriginal={capture_date}",
            f"-CreateDate={capture_date}",
            f"-ModifyDate={capture_date}",
        ]
        if ip_address:
            tags += [
                f"-EXIF:UserComment={ip_address}",
                f"-Comment={ip_address}",
            ]
    elif is_video(ext):
        tags += [
            f"-Make={device['make']}",
            f"-Model={device['model']}",
            f"-Software={device['software']}",
            f"-CreateDate={capture_date}",
            f"-ModifyDate={capture_date}",
        ]
        if ip_address:
            tags += [
                f"-Comment={ip_address}",
                f"-UserComment={ip_address}",
            ]
    else:
        tags += [
            f"-Make={device['make']}",
            f"-Model={device['model']}",
            f"-Software={device['software']}",
        ]
        if ip_address:
            tags += [f"-Comment={ip_address}"]

    _apply_gps_tags(tags, location, ext)

    tags += ["-overwrite_original", str(dst_path)]
    run_exiftool(tags)

    try:
        dt = datetime.strptime(capture_date, "%Y:%m:%d %H:%M:%S")
        set_file_dates(str(dst_path), dt.timestamp())
    except Exception:
        pass

    return dst_path


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/devices")
def devices():
    return jsonify(get_device_list())


@app.route("/api/cities")
def cities():
    return jsonify(get_city_list())


@app.route("/api/upload", methods=["POST"])
def upload():
    if not exiftool_ok():
        return jsonify({"error": "ExifTool не найден. Установите ExifTool и добавьте его в PATH."}), 500

    if "file" not in request.files:
        return jsonify({"error": "Файл не найден в запросе"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Имя файла пустое"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Неподдерживаемый формат файла"}), 400

    upload_id = uuid.uuid4().hex
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{upload_id}.{ext}"
    upload_path = UPLOAD_DIR / stored_name
    file.save(str(upload_path))

    metadata = read_file_metadata(upload_path)
    thumbnail = None
    if is_image(ext):
        thumb_name = f"{upload_id}.jpg"
        thumb_path = THUMBNAIL_DIR / thumb_name
        if make_thumbnail(upload_path, thumb_path):
            thumbnail = f"/static/thumbnails/{thumb_name}"

    return jsonify({
        "upload_id": upload_id,
        "original_name": original_name,
        "extension": ext,
        "type": "image" if is_image(ext) else "video",
        "thumbnail": thumbnail,
        "metadata": metadata,
    })


@app.route("/api/process", methods=["POST"])
def process():
    if not exiftool_ok():
        return jsonify({"error": "ExifTool не найден. Установите ExifTool и добавьте его в PATH."}), 500

    data = request.get_json()
    upload_id = data.get("upload_id")
    device_id = data.get("device_id")
    ip_address = data.get("ip_address", "").strip()
    preserve_dates = data.get("preserve_dates", True)
    location_id = data.get("location_id")
    manual_location = data.get("location")

    if not upload_id or not device_id:
        return jsonify({"error": "upload_id и device_id обязательны"}), 400

    device = get_device(device_id)
    if not device:
        return jsonify({"error": "Неизвестное устройство"}), 400

    location = None
    if location_id:
        location = get_city(location_id)
        if not location:
            return jsonify({"error": "Неизвестный город"}), 400
    elif manual_location and isinstance(manual_location, dict):
        try:
            lat = float(manual_location.get("lat", 0))
            lon = float(manual_location.get("lon", 0))
            alt = float(manual_location.get("alt", 0))
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("Некорректные координаты")
            location = {
                "city": manual_location.get("city", ""),
                "state": manual_location.get("state", ""),
                "country": manual_location.get("country", ""),
                "lat": lat,
                "lon": lon,
                "alt": alt,
            }
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Некорректные координаты: {e}"}), 400

    upload_files = list(UPLOAD_DIR.glob(f"{upload_id}.*"))
    if not upload_files:
        return jsonify({"error": "Исходный файл не найден"}), 404

    upload_path = upload_files[0]
    ext = upload_path.suffix
    processed_name = f"{upload_id}_processed{ext}"
    processed_path = PROCESSED_DIR / processed_name

    original_name = secure_filename(data.get("original_name", f"processed{ext}"))

    try:
        apply_metadata(upload_path, processed_path, device, ip_address or None, preserve_dates, location)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    new_metadata = read_file_metadata(processed_path)
    file_size = processed_path.stat().st_size

    return jsonify({
        "filename": processed_name,
        "original_name": original_name,
        "download_url": f"/api/download/{processed_name}?name={original_name}",
        "size": file_size,
        "metadata": new_metadata,
    })


@app.route("/api/download/<filename>")
def download(filename):
    file_path = PROCESSED_DIR / secure_filename(filename)
    if not file_path.exists():
        return jsonify({"error": "Файл не найден"}), 404

    download_name = secure_filename(request.args.get("name", filename))
    return send_file(
        file_path,
        as_attachment=True,
        download_name=download_name,
    )


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Файл слишком большой. Максимальный размер 500 МБ."}), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
