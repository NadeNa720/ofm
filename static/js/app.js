document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const previewSection = document.getElementById("preview-section");
    const previewMedia = document.getElementById("preview-media");
    const fileInfo = document.getElementById("file-info");
    const editorSection = document.getElementById("editor-section");
    const deviceSelect = document.getElementById("device-select");
    const ipInput = document.getElementById("ip-address");
    const preserveDatesCheckbox = document.getElementById("preserve-dates");
    const locationSelect = document.getElementById("location-select");
    const manualLocationToggle = document.getElementById("manual-location-toggle");
    const manualLocationPanel = document.getElementById("manual-location");
    const manualLat = document.getElementById("manual-lat");
    const manualLon = document.getElementById("manual-lon");
    const manualAlt = document.getElementById("manual-alt");
    const manualCity = document.getElementById("manual-city");
    const deviceInfo = document.getElementById("device-info");
    const deviceInfoList = document.getElementById("device-info-list");
    const processBtn = document.getElementById("process-btn");
    const resultSection = document.getElementById("result-section");
    const downloadBtn = document.getElementById("download-btn");
    const resetBtn = document.getElementById("reset-btn");
    const errorSection = document.getElementById("error-section");
    const errorMessage = document.getElementById("error-message");
    const errorResetBtn = document.getElementById("error-reset-btn");
    const metadataCompare = document.getElementById("metadata-compare");

    let currentUpload = null;
    let devices = [];
    let cities = [];

    loadDevices();
    loadCities();

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    deviceSelect.addEventListener("change", updateSummaryInfo);
    locationSelect.addEventListener("change", updateSummaryInfo);
    manualLocationToggle.addEventListener("change", () => {
        manualLocationPanel.classList.toggle("hidden", !manualLocationToggle.checked);
        updateSummaryInfo();
    });
    [manualLat, manualLon, manualAlt, manualCity].forEach((input) => {
        input.addEventListener("input", updateSummaryInfo);
    });
    processBtn.addEventListener("click", processFile);
    resetBtn.addEventListener("click", resetApp);
    errorResetBtn.addEventListener("click", resetApp);

    async function loadDevices() {
        try {
            const response = await fetch("/api/devices");
            devices = await response.json();
            populateDeviceSelect();
        } catch (err) {
            showError("Не удалось загрузить список устройств: " + err.message);
        }
    }

    function populateDeviceSelect() {
        deviceSelect.innerHTML = '<option value="" disabled selected>Выберите устройство</option>';
        devices.forEach((device) => {
            const option = document.createElement("option");
            option.value = device.id;
            option.textContent = device.label;
            deviceSelect.appendChild(option);
        });
    }

    async function loadCities() {
        try {
            const response = await fetch("/api/cities");
            cities = await response.json();
            populateLocationSelect();
        } catch (err) {
            console.error("Не удалось загрузить список городов:", err.message);
        }
    }

    function populateLocationSelect() {
        locationSelect.innerHTML = '<option value="">Без геолокации</option>';
        cities.forEach((city) => {
            const option = document.createElement("option");
            option.value = city.id;
            option.textContent = city.label;
            if (city.id === "new_york") {
                option.selected = true;
            }
            locationSelect.appendChild(option);
        });
    }

    function updateSummaryInfo() {
        const deviceId = deviceSelect.value;
        if (!deviceId) {
            deviceInfo.classList.add("hidden");
            processBtn.disabled = true;
            return;
        }

        const device = devices.find((d) => d.id === deviceId);
        if (!device) return;

        let html = `
            <li><strong>Производитель:</strong> ${escapeHtml(device.make)}</li>
            <li><strong>Модель:</strong> ${escapeHtml(device.model)}</li>
            <li><strong>Объектив:</strong> ${escapeHtml(device.lens_model)}</li>
            <li><strong>ПО:</strong> ${escapeHtml(device.software)}</li>
        `;

        const ipAddress = ipInput.value.trim();
        if (ipAddress) {
            html += `<li><strong>IP-адрес:</strong> ${escapeHtml(ipAddress)}</li>`;
        }

        const location = getSelectedLocation();
        if (location) {
            html += `<li><strong>Геолокация:</strong> `;
            if (location.lat !== undefined && location.lon !== undefined) {
                html += `${escapeHtml(location.lat.toFixed(4))}, ${escapeHtml(location.lon.toFixed(4))}`;
            }
            if (location.city) {
                html += location.lat !== undefined ? ` (${escapeHtml(location.city)})` : escapeHtml(location.city);
            }
            html += `</li>`;
        }

        deviceInfoList.innerHTML = html;
        deviceInfo.classList.remove("hidden");
        processBtn.disabled = false;
    }

    function getSelectedLocation() {
        if (manualLocationToggle.checked) {
            const lat = parseFloat(manualLat.value);
            const lon = parseFloat(manualLon.value);
            if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
                return {
                    lat,
                    lon,
                    alt: parseFloat(manualAlt.value) || 0,
                    city: manualCity.value.trim(),
                };
            }
        } else if (locationSelect.value) {
            const city = cities.find((c) => c.id === locationSelect.value);
            if (city) {
                return { city: city.label };
            }
        }
        return null;
    }

    async function handleFile(file) {
        resetUI();

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Ошибка загрузки файла");
            }

            currentUpload = data;
            showPreview(data, file);
            editorSection.classList.remove("hidden");
        } catch (err) {
            showError(err.message);
        }
    }

    function showPreview(data, file) {
        previewMedia.innerHTML = "";
        fileInfo.innerHTML = "";

        const isImage = data.type === "image";
        const mediaUrl = data.thumbnail || URL.createObjectURL(file);

        if (isImage) {
            const img = document.createElement("img");
            img.src = mediaUrl;
            img.alt = data.original_name;
            previewMedia.appendChild(img);
        } else {
            const video = document.createElement("video");
            video.src = URL.createObjectURL(file);
            video.controls = true;
            video.preload = "metadata";
            previewMedia.appendChild(video);
        }

        const size = formatBytes(file.size);
        fileInfo.innerHTML = `
            <p><strong>Имя файла:</strong> ${escapeHtml(data.original_name)}</p>
            <p><strong>Тип:</strong> ${isImage ? "Изображение" : "Видео"}</p>
            <p><strong>Размер:</strong> ${size}</p>
            <p><strong>Формат:</strong> ${escapeHtml(data.extension.toUpperCase())}</p>
        `;

        previewSection.classList.remove("hidden");
    }

    async function processFile() {
        if (!currentUpload) return;

        const deviceId = deviceSelect.value;
        if (!deviceId) {
            showError("Выберите устройство");
            return;
        }

        const ipAddress = ipInput.value.trim();
        if (ipAddress && !isValidIP(ipAddress)) {
            showError("Введите корректный IP-адрес");
            return;
        }

        const payload = {
            upload_id: currentUpload.upload_id,
            device_id: deviceId,
            ip_address: ipAddress,
            preserve_dates: preserveDatesCheckbox.checked,
            original_name: currentUpload.original_name,
        };

        if (manualLocationToggle.checked) {
            const lat = parseFloat(manualLat.value);
            const lon = parseFloat(manualLon.value);
            const alt = parseFloat(manualAlt.value) || 0;
            const city = manualCity.value.trim();

            if (Number.isNaN(lat) || Number.isNaN(lon)) {
                showError("Введите корректные широту и долготу");
                return;
            }
            if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
                showError("Координаты выходят за допустимые пределы");
                return;
            }
            payload.location = { lat, lon, alt, city };
        } else if (locationSelect.value) {
            payload.location_id = locationSelect.value;
        }

        processBtn.disabled = true;
        processBtn.querySelector(".btn-text").textContent = "Обработка...";
        processBtn.querySelector(".spinner").classList.remove("hidden");

        try {
            const response = await fetch("/api/process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Ошибка обработки файла");
            }

            showResult(data);
        } catch (err) {
            processBtn.disabled = false;
            showError(err.message);
        } finally {
            processBtn.querySelector(".btn-text").textContent = "Изменить метаданные";
            processBtn.querySelector(".spinner").classList.add("hidden");
        }
    }

    function showResult(data) {
        editorSection.classList.add("hidden");
        previewSection.classList.add("hidden");
        resultSection.classList.remove("hidden");

        downloadBtn.href = data.download_url;
        downloadBtn.download = data.original_name || data.filename;

        const metadataHtml = `
            <h3>Новые метаданные файла</h3>
            <pre>${escapeHtml(JSON.stringify(data.metadata, null, 2))}</pre>
        `;
        metadataCompare.innerHTML = metadataHtml;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.classList.remove("hidden");
        editorSection.classList.add("hidden");
        previewSection.classList.add("hidden");
        resultSection.classList.add("hidden");
    }

    function resetApp() {
        currentUpload = null;
        fileInput.value = "";
        deviceSelect.value = "";
        ipInput.value = "";
        preserveDatesCheckbox.checked = true;
        locationSelect.value = "";
        manualLocationToggle.checked = false;
        manualLocationPanel.classList.add("hidden");
        manualLat.value = "";
        manualLon.value = "";
        manualAlt.value = "";
        manualCity.value = "";
        deviceInfo.classList.add("hidden");
        processBtn.disabled = true;
        resetUI();
    }

    function resetUI() {
        previewSection.classList.add("hidden");
        editorSection.classList.add("hidden");
        resultSection.classList.add("hidden");
        errorSection.classList.add("hidden");
        previewMedia.innerHTML = "";
        fileInfo.innerHTML = "";
        metadataCompare.innerHTML = "";
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 Б";
        const k = 1024;
        const sizes = ["Б", "КБ", "МБ", "ГБ"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }

    function isValidIP(ip) {
        const ipv4 = /^(\d{1,3}\.){3}\d{1,3}$/;
        const ipv6 = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
        if (!ipv4.test(ip) && !ipv6.test(ip)) return false;
        if (ipv4.test(ip)) {
            return ip.split(".").every((part) => parseInt(part, 10) <= 255);
        }
        return true;
    }

    function escapeHtml(text) {
        if (text === null || text === undefined) return "";
        const div = document.createElement("div");
        div.textContent = String(text);
        return div.innerHTML;
    }
});
