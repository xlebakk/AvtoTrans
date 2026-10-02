
(function (global) {
  'use strict';


  var _map        = null;
  var _routeLayer = null;
  var _markerA    = null;
  var _markerB    = null;
  var _coordA     = null;
  var _coordB     = null;
  var _mode       = 'A';
  var _opts       = {};
  var _sTmr       = null;


  function mkIcon(letter, color) {
    return L.divIcon({
      html: '<div class="rc-marker" style="background:' + color + '">' + letter + '</div>',
      className: '',
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });
  }


  async function geocode(address) {
    var url = 'https://nominatim.openstreetmap.org/search?' +
      'q=' + encodeURIComponent(address) +
      '&format=json&limit=1&addressdetails=0';
    var r = await fetch(url, { headers: { 'Accept-Language': 'ru,en;q=0.8' } });
    var d = await r.json();
    if (!d.length) throw new Error('Адрес не найден: ' + address);
    return { lat: +d[0].lat, lon: +d[0].lon, label: d[0].display_name };
  }

  async function searchPlaces(q) {
    var url = 'https://nominatim.openstreetmap.org/search?' +
      'q=' + encodeURIComponent(q) + '&format=json&limit=6&addressdetails=0';
    var r = await fetch(url, { headers: { 'Accept-Language': 'ru,en;q=0.8' } });
    return r.json();
  }

  async function reverseGeocode(lat, lon) {
    var url = 'https://nominatim.openstreetmap.org/reverse?' +
      'lat=' + lat + '&lon=' + lon + '&format=json&zoom=12';
    var r = await fetch(url, { headers: { 'Accept-Language': 'ru,en;q=0.8' } });
    var d = await r.json();
    if (!d.display_name) return null;
    return d.display_name.split(',').slice(0, 2).join(', ').trim();
  }


  async function getRoute(a, b) {
    var url = 'https://router.project-osrm.org/route/v1/driving/' +
      a.lon + ',' + a.lat + ';' + b.lon + ',' + b.lat +
      '?overview=full&geometries=geojson';
    var r = await fetch(url);
    var d = await r.json();
    if (d.code !== 'Ok' || !d.routes.length) throw new Error('Маршрут не найден');
    var rt = d.routes[0];
    return {
      distance_km: Math.round(rt.distance / 1000),
      duration_min: Math.round(rt.duration / 60),
      geojson: rt.geometry,
    };
  }

  function fmtDur(min) {
    var h = Math.floor(min / 60), m = min % 60;
    if (h && m) return '~' + h + ' ч ' + m + ' мин';
    if (h) return '~' + h + ' ч';
    return '~' + m + ' мин';
  }


  function placeA(coord) {
    if (_markerA) _map.removeLayer(_markerA);
    _coordA = coord;
    _markerA = L.marker([coord.lat, coord.lon], { icon: mkIcon('А', 'linear-gradient(135deg,#3fb950,#2ea043)'), draggable: true })
      .bindTooltip(shortLabel(coord.label || 'Откуда'), { direction: 'top', permanent: false })
      .addTo(_map);
    _markerA.on('dragend', function (e) {
      var ll = e.target.getLatLng();
      reverseGeocode(ll.lat, ll.lng).then(function (lbl) {
        _coordA = { lat: ll.lat, lon: ll.lng, label: lbl || '' };
        syncInputA(_coordA.label);
        if (_coordB) calcRoute();
      });
    });
    syncInputA(coord.label || '');
  }

  function placeB(coord) {
    if (_markerB) _map.removeLayer(_markerB);
    _coordB = coord;
    _markerB = L.marker([coord.lat, coord.lon], { icon: mkIcon('Б', 'linear-gradient(135deg,#f85149,#cf222e)'), draggable: true })
      .bindTooltip(shortLabel(coord.label || 'Куда'), { direction: 'top', permanent: false })
      .addTo(_map);
    _markerB.on('dragend', function (e) {
      var ll = e.target.getLatLng();
      reverseGeocode(ll.lat, ll.lng).then(function (lbl) {
        _coordB = { lat: ll.lat, lon: ll.lng, label: lbl || '' };
        syncInputB(_coordB.label);
        if (_coordA) calcRoute();
      });
    });
    syncInputB(coord.label || '');
  }

  function shortLabel(l) {
    if (!l) return '';
    return l.split(',').slice(0, 2).join(', ').trim();
  }

  function syncInputA(label) {
    var el = document.getElementById('inp-origin');
    if (el && label) el.value = shortLabel(label);
  }
  function syncInputB(label) {
    var el = document.getElementById('inp-dest');
    if (el && label) el.value = shortLabel(label);
  }


  async function calcRoute() {
    if (!_coordA || !_coordB) {
      setStatus('Укажите обе точки на карте', '#f85149');
      return null;
    }
    setStatus('Строим маршрут…', '#d29922');
    try {
      var route = await getRoute(_coordA, _coordB);


      if (_routeLayer) _map.removeLayer(_routeLayer);
      _routeLayer = L.geoJSON(route.geojson, {
        style: { color: '#2f81f7', weight: 5, opacity: 0.9, lineCap: 'round', lineJoin: 'round' },
      }).addTo(_map);
      var bounds = _routeLayer.getBounds()
        .extend([_coordA.lat, _coordA.lon])
        .extend([_coordB.lat, _coordB.lon]);
      _map.fitBounds(bounds, { padding: [60, 60], maxZoom: 12 });


      var badge = document.getElementById('route-distance-badge');
      var dur   = document.getElementById('route-duration');
      if (badge) badge.textContent = route.distance_km + ' км';
      if (dur)   dur.textContent   = fmtDur(route.duration_min);
      setStatus('Маршрут: ' + route.distance_km + ' км · ' + fmtDur(route.duration_min), '#3fb950');


      document.querySelectorAll('[name="distance_km"]').forEach(function (inp) {
        if (!inp.value || inp.value === '0') inp.value = route.distance_km;
        else inp.value = route.distance_km;
      });
      return route;
    } catch (e) {
      setStatus('Ошибка: ' + e.message, '#f85149');
      return null;
    }
  }

  function setStatus(msg, color) {
    var el = document.getElementById('route-status');
    if (el) { el.textContent = msg; el.style.color = color || 'var(--text-3)'; }
  }


  function setMode(m) {
    _mode = m;
    var btnA = document.getElementById('rc-btn-a');
    var btnB = document.getElementById('rc-btn-b');
    if (btnA) btnA.classList.toggle('rc-mode-active', m === 'A');
    if (btnB) btnB.classList.toggle('rc-mode-active', m === 'B');
    var hint = document.getElementById('rc-mode-hint');
    if (hint) {
      hint.textContent = m === 'A'
        ? '📍 Кликните по карте — точка отправления (А)'
        : '🏁 Кликните по карте — точка доставки (Б)';
    }
    if (_map) _map.getContainer().style.cursor = 'crosshair';
  }


  var SearchCtrl = L.Control.extend({
    options: { position: 'topleft' },
    onAdd: function () {
      var wrap = L.DomUtil.create('div', 'rc-search-wrap leaflet-bar');
      wrap.innerHTML =
        '<div class="rc-search-row">' +
          '<span class="rc-search-icon">🔍</span>' +
          '<input id="rc-search-inp" class="rc-search-inp" type="text" placeholder="Поиск места, города, адреса…" autocomplete="off" spellcheck="false">' +
          '<button id="rc-search-x" class="rc-search-x" title="Очистить" tabindex="-1">✕</button>' +
        '</div>' +
        '<div id="rc-search-res" class="rc-search-res"></div>';
      L.DomEvent.disableClickPropagation(wrap);
      L.DomEvent.disableScrollPropagation(wrap);
      return wrap;
    },
  });


  var ModeCtrl = L.Control.extend({
    options: { position: 'bottomleft' },
    onAdd: function () {
      var div = L.DomUtil.create('div', 'rc-mode-wrap');
      div.innerHTML =
        '<button id="rc-btn-a" class="rc-mode-btn rc-mode-active">📍 Откуда (А)</button>' +
        '<button id="rc-btn-b" class="rc-mode-btn">🏁 Куда (Б)</button>' +
        '<div id="rc-mode-hint" class="rc-mode-hint">Кликните по карте — точка отправления (А)</div>';
      L.DomEvent.disableClickPropagation(div);
      return div;
    },
  });


  var LocCtrl = L.Control.extend({
    options: { position: 'topright' },
    onAdd: function () {
      var btn = L.DomUtil.create('button', 'rc-loc-btn leaflet-bar');
      btn.innerHTML = '📍';
      btn.title = 'Моё местоположение';
      L.DomEvent.on(btn, 'click', function (e) {
        L.DomEvent.stopPropagation(e);
        myLocation();
      });
      return btn;
    },
  });


  function myLocation() {
    if (!navigator.geolocation) {
      setStatus('Браузер не поддерживает геолокацию', '#f85149');
      return;
    }
    setStatus('Определяем местоположение…', '#d29922');
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        var lat = pos.coords.latitude, lon = pos.coords.longitude;
        _map.setView([lat, lon], 13);
        setStatus('Геолокация получена, определяем адрес…', '#d29922');
        reverseGeocode(lat, lon).then(function (lbl) {
          var coord = { lat: lat, lon: lon, label: lbl || (lat.toFixed(4) + ', ' + lon.toFixed(4)) };
          if (_mode === 'A') {
            placeA(coord);
            setMode('B');
            if (_coordB) calcRoute();
            else setStatus('Ваше местоположение задано (А). Укажите точку доставки (Б).', '#d29922');
          } else {
            placeB(coord);
            setMode('A');
            if (_coordA) calcRoute();
            else setStatus('Точка доставки задана (Б). Укажите точку отправления (А).', '#d29922');
          }
        });
      },
      function (err) {
        var msgs = {
          1: 'Доступ к геолокации запрещён',
          2: 'Местоположение недоступно',
          3: 'Время ожидания истекло',
        };
        setStatus(msgs[err.code] || err.message, '#f85149');
      },
      { timeout: 10000, maximumAge: 60000, enableHighAccuracy: false }
    );
  }


  function bindSearch() {
    var inp = document.getElementById('rc-search-inp');
    var res = document.getElementById('rc-search-res');
    var clr = document.getElementById('rc-search-x');
    if (!inp) return;

    inp.addEventListener('input', function () {
      clearTimeout(_sTmr);
      var q = inp.value.trim();
      if (q.length < 2) { res.innerHTML = ''; return; }
      res.innerHTML = '<div class="rc-no-result">Ищем…</div>';
      _sTmr = setTimeout(function () { doSearch(q, res, inp); }, 350);
    });

    inp.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { res.innerHTML = ''; inp.value = ''; }
    });

    if (clr) clr.addEventListener('click', function () { inp.value = ''; res.innerHTML = ''; });


    document.addEventListener('click', function (e) {
      var wrap = document.querySelector('.rc-search-wrap');
      if (wrap && !wrap.contains(e.target)) res.innerHTML = '';
    });
  }

  async function doSearch(query, resEl, inp) {
    try {
      var items = await searchPlaces(query);
      resEl.innerHTML = '';
      if (!items.length) {
        resEl.innerHTML = '<div class="rc-no-result">Ничего не найдено</div>';
        return;
      }
      items.forEach(function (item) {
        var d = document.createElement('div');
        d.className = 'rc-search-item';
        var name = item.display_name.split(',').slice(0, 3).join(', ');
        var type = item.type || '';
        d.innerHTML =
          '<span class="rc-item-name">' + escHtml(name) + '</span>' +
          (type ? '<span class="rc-item-type">' + escHtml(type) + '</span>' : '');
        d.title = item.display_name;

        d.addEventListener('mousedown', function (e) {
          e.preventDefault();
          var coord = { lat: +item.lat, lon: +item.lon, label: item.display_name };
          _map.setView([coord.lat, coord.lon], 13);
          if (_mode === 'A') {
            placeA(coord);
            setMode('B');
            if (_coordB) calcRoute();
            else setStatus('Точка А задана. Теперь укажите Б на карте или через поиск.', '#d29922');
          } else {
            placeB(coord);
            setMode('A');
            if (_coordA) calcRoute();
            else setStatus('Точка Б задана. Теперь укажите А на карте или через поиск.', '#d29922');
          }
          inp.value = '';
          resEl.innerHTML = '';
        });
        resEl.appendChild(d);
      });
    } catch (e) {
      resEl.innerHTML = '<div class="rc-no-result">Ошибка: ' + escHtml(e.message) + '</div>';
    }
  }

  function escHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }


  function init(opts) {
    _opts = opts || {};
    var containerId = _opts.mapId || 'route-map';
    var readOnly = !!_opts.readonly;

    if (_map) { _map.remove(); _map = _routeLayer = _markerA = _markerB = null; _coordA = _coordB = null; }

    _map = L.map(containerId, { center: [55.0, 60.0], zoom: 4, zoomControl: false });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(_map);


    L.control.zoom({ position: 'bottomright' }).addTo(_map);


    new LocCtrl().addTo(_map);

    if (!readOnly) {

      new SearchCtrl().addTo(_map);
      new ModeCtrl().addTo(_map);


      setTimeout(function () {
        bindSearch();
        var btnA = document.getElementById('rc-btn-a');
        var btnB = document.getElementById('rc-btn-b');
        if (btnA) btnA.addEventListener('click', function () { setMode('A'); });
        if (btnB) btnB.addEventListener('click', function () { setMode('B'); });
        setMode('A');
      }, 0);


      _map.on('click', function (e) {
        var lat = e.latlng.lat, lon = e.latlng.lng;
        setStatus('Определяем адрес точки…', '#d29922');
        reverseGeocode(lat, lon).then(function (lbl) {
          var coord = { lat: lat, lon: lon, label: lbl || (lat.toFixed(5) + ', ' + lon.toFixed(5)) };
          if (_mode === 'A') {
            placeA(coord);
            setMode('B');
            if (_coordB) calcRoute();
            else setStatus('Точка А задана. Укажите точку Б (клик или поиск).', '#d29922');
          } else {
            placeB(coord);
            setMode('A');
            if (_coordA) calcRoute();
            else setStatus('Точка Б задана. Укажите точку А (клик или поиск).', '#d29922');
          }
        });
      });


      ['inp-origin', 'inp-dest'].forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('keydown', function (e) {
          if (e.key !== 'Enter') return;
          e.preventDefault();
          var addr = el.value.trim();
          if (!addr) return;
          setStatus('Геокодируем «' + addr + '»…', '#d29922');
          geocode(addr).then(function (coord) {
            _map.setView([coord.lat, coord.lon], 10);
            if (id === 'inp-origin') { placeA(coord); if (_coordB) calcRoute(); }
            else                     { placeB(coord); if (_coordA) calcRoute(); }
          }).catch(function (err) { setStatus(err.message, '#f85149'); });
        });
      });
    } else {

      _map.getContainer().style.cursor = 'default';
    }


    var origin = _opts.origin || '';
    var dest   = _opts.dest   || '';
    if (origin && dest) {
      setStatus('Загружаем маршрут…', '#d29922');
      Promise.all([geocode(origin), geocode(dest)]).then(function (coords) {
        placeA(coords[0], readOnly);
        placeB(coords[1], readOnly);
        return calcRoute();
      }).catch(function (e) { setStatus(e.message, '#f85149'); });
    } else if (origin) {
      geocode(origin).then(function (c) {
        placeA(c, readOnly);
        _map.setView([c.lat, c.lon], 8);
        if (!readOnly) { setMode('B'); setStatus('Введите или кликните точку доставки (Б)', '#d29922'); }
      }).catch(function () {});
    }
  }


  function enableEdit() {
    if (!_map) return;
    _map.getContainer().style.cursor = 'crosshair';

    if (!document.getElementById('rc-search-inp')) new SearchCtrl().addTo(_map);
    if (!document.getElementById('rc-btn-a'))      new ModeCtrl().addTo(_map);
    setTimeout(function () {
      bindSearch();
      var btnA = document.getElementById('rc-btn-a');
      var btnB = document.getElementById('rc-btn-b');
      if (btnA) btnA.addEventListener('click', function () { setMode('A'); });
      if (btnB) btnB.addEventListener('click', function () { setMode('B'); });
      setMode('B');
    }, 0);
    _map.on('click', function (e) {
      var lat = e.latlng.lat, lon = e.latlng.lng;
      setStatus('Определяем адрес…', '#d29922');
      reverseGeocode(lat, lon).then(function (lbl) {
        var coord = { lat: lat, lon: lon, label: lbl || (lat.toFixed(5) + ', ' + lon.toFixed(5)) };
        if (_mode === 'A') { placeA(coord); setMode('B'); if (_coordB) calcRoute(); }
        else               { placeB(coord); setMode('A'); if (_coordA) calcRoute(); }
      });
    });

    if (_markerA) _markerA.dragging && _markerA.dragging.enable();
    if (_markerB) _markerB.dragging && _markerB.dragging.enable();
    setStatus('Режим редактирования включён. Кликните по карте для изменения маршрута.', '#2f81f7');
  }


  global.RouteCalc = {
    init: init,
    enableEdit: enableEdit,
    calcRoute: calcRoute,
    geocode: geocode,
    myLocation: myLocation,
    setMode: setMode,
    get map() { return _map; },


    recalcFromInputs: function () {
      var a = (document.getElementById('inp-origin') || {}).value || '';
      var b = (document.getElementById('inp-dest')   || {}).value || '';
      if (!a || !b) { setStatus('Укажите оба адреса', '#f85149'); return; }
      setStatus('Геокодируем адреса…', '#d29922');
      Promise.all([geocode(a), geocode(b)]).then(function (coords) {
        placeA(coords[0]);
        placeB(coords[1]);
        _map.setView([coords[0].lat, coords[0].lon], 5);
        return calcRoute();
      }).catch(function (e) { setStatus(e.message, '#f85149'); });
    },
  };
})(window);
