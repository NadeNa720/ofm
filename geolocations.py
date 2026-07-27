CITIES = {
    "new_york": {
        "label": "New York, USA",
        "city": "New York City",
        "state": "New York",
        "country": "USA",
        "lat": 40.7143,
        "lon": -74.0060,
        "alt": 10,
    },
    "los_angeles": {
        "label": "Los Angeles, USA",
        "city": "Los Angeles",
        "state": "California",
        "country": "USA",
        "lat": 34.0522,
        "lon": -118.2437,
        "alt": 89,
    },
    "london": {
        "label": "London, UK",
        "city": "London",
        "state": "England",
        "country": "United Kingdom",
        "lat": 51.5074,
        "lon": -0.1278,
        "alt": 11,
    },
    "paris": {
        "label": "Paris, France",
        "city": "Paris",
        "state": "Île-de-France",
        "country": "France",
        "lat": 48.8566,
        "lon": 2.3522,
        "alt": 35,
    },
    "tokyo": {
        "label": "Tokyo, Japan",
        "city": "Tokyo",
        "state": "Tokyo",
        "country": "Japan",
        "lat": 35.6762,
        "lon": 139.6503,
        "alt": 40,
    },
    "berlin": {
        "label": "Berlin, Germany",
        "city": "Berlin",
        "state": "Berlin",
        "country": "Germany",
        "lat": 52.5200,
        "lon": 13.4050,
        "alt": 34,
    },
    "moscow": {
        "label": "Moscow, Russia",
        "city": "Moscow",
        "state": "Moscow",
        "country": "Russia",
        "lat": 55.7558,
        "lon": 37.6173,
        "alt": 156,
    },
    "dubai": {
        "label": "Dubai, UAE",
        "city": "Dubai",
        "state": "Dubai",
        "country": "United Arab Emirates",
        "lat": 25.2048,
        "lon": 55.2708,
        "alt": 5,
    },
    "sydney": {
        "label": "Sydney, Australia",
        "city": "Sydney",
        "state": "New South Wales",
        "country": "Australia",
        "lat": -33.8688,
        "lon": 151.2093,
        "alt": 19,
    },
    "singapore": {
        "label": "Singapore",
        "city": "Singapore",
        "state": "Singapore",
        "country": "Singapore",
        "lat": 1.3521,
        "lon": 103.8198,
        "alt": 15,
    },
    "hong_kong": {
        "label": "Hong Kong",
        "city": "Hong Kong",
        "state": "Hong Kong",
        "country": "China",
        "lat": 22.3193,
        "lon": 114.1694,
        "alt": 0,
    },
    "toronto": {
        "label": "Toronto, Canada",
        "city": "Toronto",
        "state": "Ontario",
        "country": "Canada",
        "lat": 43.6532,
        "lon": -79.3832,
        "alt": 76,
    },
    "mumbai": {
        "label": "Mumbai, India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "lat": 19.0760,
        "lon": 72.8777,
        "alt": 14,
    },
    "rio_de_janeiro": {
        "label": "Rio de Janeiro, Brazil",
        "city": "Rio de Janeiro",
        "state": "Rio de Janeiro",
        "country": "Brazil",
        "lat": -22.9068,
        "lon": -43.1729,
        "alt": 0,
    },
    "rome": {
        "label": "Rome, Italy",
        "city": "Rome",
        "state": "Lazio",
        "country": "Italy",
        "lat": 41.9028,
        "lon": 12.4964,
        "alt": 37,
    },
    "madrid": {
        "label": "Madrid, Spain",
        "city": "Madrid",
        "state": "Community of Madrid",
        "country": "Spain",
        "lat": 40.4168,
        "lon": -3.7038,
        "alt": 667,
    },
    "amsterdam": {
        "label": "Amsterdam, Netherlands",
        "city": "Amsterdam",
        "state": "North Holland",
        "country": "Netherlands",
        "lat": 52.3676,
        "lon": 4.9041,
        "alt": -2,
    },
    "istanbul": {
        "label": "Istanbul, Turkey",
        "city": "Istanbul",
        "state": "Istanbul",
        "country": "Turkey",
        "lat": 41.0082,
        "lon": 28.9784,
        "alt": 39,
    },
    "seoul": {
        "label": "Seoul, South Korea",
        "city": "Seoul",
        "state": "Seoul",
        "country": "South Korea",
        "lat": 37.5665,
        "lon": 126.9780,
        "alt": 38,
    },
    "mexico_city": {
        "label": "Mexico City, Mexico",
        "city": "Mexico City",
        "state": "Mexico City",
        "country": "Mexico",
        "lat": 19.4326,
        "lon": -99.1332,
        "alt": 2240,
    },
    "warsaw": {
        "label": "Warsaw, Poland",
        "city": "Warsaw",
        "state": "Masovian Voivodeship",
        "country": "Poland",
        "lat": 52.2297,
        "lon": 21.0122,
        "alt": 100,
    },
    "kyiv": {
        "label": "Kyiv, Ukraine",
        "city": "Kyiv",
        "state": "Kyiv",
        "country": "Ukraine",
        "lat": 50.4501,
        "lon": 30.5234,
        "alt": 179,
    },
    "minsk": {
        "label": "Minsk, Belarus",
        "city": "Minsk",
        "state": "Minsk",
        "country": "Belarus",
        "lat": 53.9045,
        "lon": 27.5615,
        "alt": 222,
    },
}


def get_city_list():
    return [{"id": k, "label": v["label"]} for k, v in CITIES.items()]


def get_city(city_id):
    return CITIES.get(city_id)


def format_dms(deg, is_lat):
    """Преобразует десятичные градусы в формат DMS для EXIF GPS."""
    abs_deg = abs(deg)
    d = int(abs_deg)
    m_float = (abs_deg - d) * 60
    m = int(m_float)
    s = round((m_float - m) * 60, 3)
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    ref = "N" if is_lat and deg >= 0 else "S" if is_lat else "E" if deg >= 0 else "W"
    return f'{d} {m} {s}"', ref
