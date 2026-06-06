#----------------------
#1. LOAD AND PROCESS
#----------------------
import pandas as pd
import math
import json
import unicodedata

def load_and_process(json_path, continent, country, city):
    with open(json_path, 'r', encoding='utf-8') as f:
        flat_data = json.load(f)

    # Transformar lista plana a tu estructura de diccionario esperada
    data = {}
    for l in flat_data:
        c, cou, cit = l['continent'], l['country'], l['city']
        data.setdefault(c, {}).setdefault(cou, {}).setdefault(cit, {'landmarks': []})

        # Mapear 'latitude'/'longitude' a 'lat'/'lon' para que los otros bloques funcionen
        l_copy = l.copy()
        l_copy['lat'] = l_copy.pop('latitude')
        l_copy['lon'] = l_copy.pop('longitude')
        data[c][cou][cit]['landmarks'].append(l_copy)

    norm = lambda x: unicodedata.normalize('NFKD', x).encode('ASCII', 'ignore').decode('utf-8')
    city_data = None
    for c in data.get(continent, {}).get(country, {}):
        if norm(c) == norm(city):
            city_data = data[continent][country][c]
            break
    if not city_data: return None

    landmarks = city_data.get('landmarks', [])
    lat_avg = sum(l['lat'] for l in landmarks) / len(landmarks)
    lon_avg = sum(l['lon'] for l in landmarks) / len(landmarks)

    for l in landmarks:
        dlat, dlon = math.radians(l['lat'] - lat_avg), math.radians(l['lon'] - lon_avg)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat_avg)) * math.cos(math.radians(l['lat'])) * math.sin(dlon/2)**2
        dist = 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        l['is_outlier'] = dist > 20
    return landmarks

#----------------------
#2. GET ESSENTIALS
#----------------------
def get_essentials(landmarks):
    # Filter only urban
    urban = sorted([l for l in landmarks if not l['is_outlier']], key=lambda x: x['priority'])

    # Logic: 1 day if small, 2 if dense
    days_needed = 1 if len(urban) <= 10 else 2
    per_day = min(math.ceil(len(urban) / days_needed), 6)

    # Arrange routes
    sorted_by_geo = sorted(urban, key=lambda x: x['lat'], reverse=True)

    result = {}
    for i in range(days_needed):
        result[f"Day {i+1} (Geo Zone)"] = sorted_by_geo[i*per_day : (i+1)*per_day]
    return result

#----------------------
#3. GET ACADEMIC
#----------------------
def get_academic(landmarks):
    urban = sorted([l for l in landmarks if not l['is_outlier']], key=lambda x: x['priority'])
    excursions = [l for l in landmarks if l['is_outlier']]

    # Clusters per day
    num_days = math.ceil(len(urban) / 6)
    sorted_u = sorted(urban, key=lambda x: x['lat'], reverse=True)

    report = {"urban_days": {}, "excursions": excursions}
    for i in range(num_days):
        report["urban_days"][f"Day {i+1}"] = sorted_u[i*6 : (i+1)*6]
    return report

#----------------------
#4. FORMAT FOR MAP
#----------------------
def format_for_map(day_landmarks):
    return [
        {
            "name": l.get('landmark', 'Sin nombre'),
            "lat": l['lat'],
            "lon": l['lon'],
            "architect": l.get('architect', 'Desconocido'),
            "priority": l.get('priority', 0)
        }
        for l in day_landmarks
    ]

#----------------------
#5. GET NAVIGATION DATA
#----------------------
def get_navigation_index(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    index = {}
    for l in data:
        cont, cou, cit = l['continent'], l['country'], l['city']
        # Filtramos para evitar que el país sea igual a la ciudad (limpieza de datos)
        if cou.lower() != cit.lower():
            index.setdefault(cont, {}).setdefault(cou, set()).add(cit)

    # Convertimos los sets a listas ordenadas alfabéticamente
    return {c: {cou: sorted(list(cits)) for cou, cits in countries.items()}
            for c, countries in index.items()}

# Pruébalo ahora
navigation_index = get_navigation_index('tta_destinations.json')
print(navigation_index)

