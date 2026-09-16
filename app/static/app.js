(function () {
  const maps = {};
  const defaultCenter = [41.3111, 69.2797];

  function statusFor(kind, text, isError = false) {
    const status = document.querySelector(`[data-map-status="${kind}"]`);
    if (!status) return;
    status.textContent = text;
    status.classList.toggle("error", isError);
  }

  function setPoint(kind, lat, lng, replaceText = false) {
    const field = document.querySelector(`[data-map-field="${kind}"]`);
    if (!field) return;

    const inputName = kind === "origin" ? "origin" : "destination";
    const textInput = field.querySelector(`input[name="${inputName}"]`);
    const latInput = field.querySelector(`input[name="${kind}_lat"]`);
    const lngInput = field.querySelector(`input[name="${kind}_lng"]`);
    const coordinatesText = `Координаты: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;

    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
    if (replaceText || !textInput.value.trim()) {
      textInput.value = coordinatesText;
    }
    statusFor(kind, coordinatesText);
  }

  function openMap(kind) {
    if (!window.L) {
      statusFor(kind, "Карта не загрузилась. Адрес можно написать вручную.", true);
      return;
    }

    const mapBox = document.getElementById(`${kind}-map`);
    if (!mapBox) return;
    mapBox.classList.add("open");

    if (!maps[kind]) {
      const map = L.map(mapBox).setView(defaultCenter, 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
      }).addTo(map);

      const marker = L.marker(defaultCenter, { draggable: true }).addTo(map);
      marker.on("dragend", function () {
        const position = marker.getLatLng();
        setPoint(kind, position.lat, position.lng, true);
      });
      map.on("click", function (event) {
        marker.setLatLng(event.latlng);
        setPoint(kind, event.latlng.lat, event.latlng.lng, true);
      });

      maps[kind] = { map, marker };
    }

    setTimeout(() => maps[kind].map.invalidateSize(), 50);
  }

  document.querySelectorAll("[data-open-map]").forEach((button) => {
    button.addEventListener("click", () => openMap(button.dataset.openMap));
  });

  document.querySelectorAll("[data-map-field]").forEach((field) => {
    const kind = field.dataset.mapField;
    const inputName = kind === "origin" ? "origin" : "destination";
    const input = field.querySelector(`input[name="${inputName}"]`);
    if (input) {
      input.addEventListener("focus", () => openMap(kind));
    }
  });

  document.querySelectorAll("[data-use-location]").forEach((button) => {
    button.addEventListener("click", () => {
      const kind = button.dataset.useLocation;
      openMap(kind);
      statusFor(kind, "Определяем местоположение...");

      if (!navigator.geolocation) {
        statusFor(kind, "Браузер не поддерживает геолокацию. Выберите точку на карте или напишите адрес.", true);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          maps[kind].map.setView([latitude, longitude], 15);
          maps[kind].marker.setLatLng([latitude, longitude]);
          setPoint(kind, latitude, longitude, true);
        },
        (error) => {
          const messages = {
            1: "Доступ к геолокации запрещён. Разрешите доступ в браузере или выберите точку на карте.",
            2: "Не удалось определить место. Выберите точку на карте или напишите адрес.",
            3: "Геолокация долго не отвечает. Выберите точку на карте или напишите адрес.",
          };
          statusFor(kind, messages[error.code] || "Геолокация не сработала. Можно выбрать точку на карте.", true);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
      );
    });
  });

  document.querySelectorAll("[data-category-select]").forEach((select) => {
    const custom = document.querySelector("[data-category-custom]");
    function syncCustomField() {
      if (!custom) return;
      custom.hidden = select.value !== "__custom__";
      custom.required = select.value === "__custom__";
    }
    select.addEventListener("change", syncCustomField);
    syncCustomField();
  });
})();

