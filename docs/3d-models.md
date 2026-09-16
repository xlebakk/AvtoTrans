# Бесплатные 3D-модели машин

Приложение автоматически ищет локальную модель:

```text
app/static/models/model.dae
```

Если её нет, ищет:

```text
app/static/models/truck.glb
```

Если файл есть, карточки машин показывают его. Если файлов нет, показывается встроенная простая 3D-модель грузовика.

## Где скачать бесплатно

1. Kenney Car Kit  
   https://kenney.nl/assets/car-kit  
   Лицензия: Creative Commons CC0.

2. Quaternius Cars Pack  
   https://quaternius.com/packs/cars.html  
   Бесплатно для личных и коммерческих проектов. На странице есть форматы FBX, OBJ, Blend.

3. Quaternius Cars Bundle на Poly Pizza  
   https://poly.pizza/bundle/Cars-Bundle-FE5IWe6OMk  
   Есть GLTF/GLB-вариант, лицензия CC0.

4. Kenney Car Kit GLB Pack на itch.io  
   https://eclair-assets.itch.io/car-kit-glb-pack-50-free-cc0-3d-models  
   Удобный GLB-пак на основе Kenney Car Kit.

## Как подключить

Скачайте модель в формате `.dae`, переименуйте её в:

```text
model.dae
```

или скачайте модель в формате `.glb`, переименуйте её в:

```text
truck.glb
```

и положите в:

```text
app/static/models/
```

После перезагрузки страницы 3D-просмотрщик начнёт использовать скачанную модель.
