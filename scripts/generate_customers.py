from faker import Faker
import csv
import random
import sys
import json

fake = Faker("en_US")
Faker.seed(42)
random.seed(42)

num_records = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

# Home locations with geographic metadata for realistic travel patterns
LOCATION_POOLS = {
    "New York": {
        "state": "NY",
        "zip": "10001",
        "region": "east_coast",
        "lat": 40.7128,
        "lng": -74.0060,
        "ip_ranges": [(64, 71), (72, 75), (96, 99)],  # Verizon, Spectrum East
        "weight": 35,
    },
    "Los Angeles": {
        "state": "CA",
        "zip": "90001",
        "region": "west_coast",
        "lat": 34.0522,
        "lng": -118.2437,
        "ip_ranges": [(66, 69), (76, 79), (104, 107)],  # AT&T, Charter West
        "weight": 25,
    },
    "Chicago": {
        "state": "IL",
        "zip": "60601",
        "region": "midwest",
        "lat": 41.8781,
        "lng": -87.6298,
        "ip_ranges": [(70, 73), (98, 101)],  # Comcast Midwest
        "weight": 15,
    },
    "Houston": {
        "state": "TX",
        "zip": "77001",
        "region": "south",
        "lat": 29.7604,
        "lng": -95.3698,
        "ip_ranges": [(74, 77), (108, 111)],  # AT&T South
        "weight": 15,
    },
    "Phoenix": {
        "state": "AZ",
        "zip": "85001",
        "region": "southwest",
        "lat": 33.4484,
        "lng": -112.0740,
        "ip_ranges": [(68, 71), (100, 103)],  # Cox Southwest
        "weight": 6,
    },
    "Philadelphia": {
        "state": "PA",
        "zip": "19101",
        "region": "east_coast",
        "lat": 39.9526,
        "lng": -75.1652,
        "ip_ranges": [(65, 68), (97, 100)],  # Comcast East
        "weight": 4,
    },
}

# Age groups with realistic US population distribution (starting at 18)
AGE_GROUPS = [
    (18, 24),  # 12% - Young adults, college age
    (25, 34),  # 18% - Early career
    (35, 44),  # 17% - Mid career
    (45, 54),  # 16% - Established professionals
    (55, 64),  # 15% - Late career
    (65, 74),  # 12% - Early retirement
    (75, 85),  # 7% - Senior
    (86, 95),  # 3% - Elderly
]
AGE_WEIGHTS = [12, 18, 17, 16, 15, 12, 7, 3]

# Marital status options with age-correlated distribution
MARITAL_STATUS = {
    "Single": {"base_weight": 30},
    "Married": {"base_weight": 45},
    "Divorced": {"base_weight": 12},
    "Widowed": {"base_weight": 5},
    "Separated": {"base_weight": 4},
    "Domestic Partnership": {"base_weight": 4},
}

# Age-based marital status adjustments (more realistic distributions)
MARITAL_BY_AGE = {
    (18, 24): {
        "Single": 75,
        "Married": 8,
        "Divorced": 1,
        "Widowed": 0,
        "Separated": 1,
        "Domestic Partnership": 15,
    },
    (25, 34): {
        "Single": 45,
        "Married": 40,
        "Divorced": 5,
        "Widowed": 0,
        "Separated": 3,
        "Domestic Partnership": 7,
    },
    (35, 44): {
        "Single": 20,
        "Married": 55,
        "Divorced": 15,
        "Widowed": 1,
        "Separated": 5,
        "Domestic Partnership": 4,
    },
    (45, 54): {
        "Single": 12,
        "Married": 58,
        "Divorced": 20,
        "Widowed": 3,
        "Separated": 4,
        "Domestic Partnership": 3,
    },
    (55, 64): {
        "Single": 8,
        "Married": 60,
        "Divorced": 18,
        "Widowed": 8,
        "Separated": 3,
        "Domestic Partnership": 3,
    },
    (65, 74): {
        "Single": 5,
        "Married": 55,
        "Divorced": 15,
        "Widowed": 20,
        "Separated": 2,
        "Domestic Partnership": 3,
    },
    (75, 85): {
        "Single": 4,
        "Married": 40,
        "Divorced": 10,
        "Widowed": 42,
        "Separated": 1,
        "Domestic Partnership": 3,
    },
    (86, 95): {
        "Single": 3,
        "Married": 25,
        "Divorced": 7,
        "Widowed": 62,
        "Separated": 1,
        "Domestic Partnership": 2,
    },
}

# Income ranges by marital status (household income)
# Single person incomes tend to be lower (one earner)
INCOME_SINGLE = [
    25000,  # 15% - Entry level/part-time
    35000,  # 20% - Early career
    50000,  # 25% - Mid career single
    70000,  # 20% - Professional single
    95000,  # 12% - Senior professional
    130000,  # 5% - Executive single
    180000,  # 3% - High earner
]
INCOME_SINGLE_WEIGHTS = [15, 20, 25, 20, 12, 5, 3]

# Married/partnered household incomes (dual income potential)
INCOME_MARRIED = [
    45000,  # 10% - Single income household
    65000,  # 15% - One full + one part-time
    85000,  # 22% - Dual modest income
    110000,  # 20% - Dual professional
    145000,  # 15% - Upper middle class
    190000,  # 10% - Dual high earners
    250000,  # 5% - Executive household
    350000,  # 3% - Top earners
]
INCOME_MARRIED_WEIGHTS = [10, 15, 22, 20, 15, 10, 5, 3]

# Divorced/Separated incomes (often reduced from married)
INCOME_DIVORCED = [
    30000,  # 18% - Post-divorce adjustment
    45000,  # 22% - Rebuilding
    60000,  # 25% - Stabilized
    80000,  # 18% - Recovered
    105000,  # 10% - Professional
    140000,  # 5% - High earner
    200000,  # 2% - Executive
]
INCOME_DIVORCED_WEIGHTS = [18, 22, 25, 18, 10, 5, 2]

# Widowed incomes (often on fixed income/retirement)
INCOME_WIDOWED = [
    22000,  # 20% - Social security only
    35000,  # 25% - SS + small pension
    50000,  # 25% - Pension + savings
    70000,  # 15% - Good retirement
    95000,  # 10% - Comfortable
    130000,  # 4% - Wealthy
    180000,  # 1% - Very wealthy
]
INCOME_WIDOWED_WEIGHTS = [20, 25, 25, 15, 10, 4, 1]

# Gender options with realistic distribution
GENDERS = ["Male", "Female", "Non-binary", "Prefer not to say"]
GENDER_WEIGHTS = [48, 48, 2, 2]

# Race categories (US Census based with realistic distribution)
RACES = [
    "White",
    "Black or African American",
    "Asian",
    "American Indian or Alaska Native",
    "Native Hawaiian or Pacific Islander",
    "Two or More Races",
]
# US Census 2020 approximate distribution
RACE_WEIGHTS = [58, 12, 6, 1, 0.5, 4]

# Ethnicity (Hispanic/Latino is tracked separately from race per US Census)
ETHNICITIES = [
    "Not Hispanic or Latino",
    "Hispanic or Latino - Mexican",
    "Hispanic or Latino - Dominican",
    "Hispanic or Latino - Cuban",
    "Hispanic or Latino - Other",
]
# US Census 2020 approximate distribution (~18.5% Hispanic)
ETHNICITY_WEIGHTS = [81.5, 11, 2, 1, 3.5]

# Regional variations in demographics (more realistic geographic distribution)
REGIONAL_RACE_WEIGHTS = {
    "east_coast": [55, 15, 8, 0.5, 0.3, 5],  # More diverse
    "west_coast": [45, 6, 15, 1, 1.5, 8],  # Higher Asian, Pacific Islander
    "midwest": [72, 10, 3, 1, 0.2, 3],  # Higher White
    "south": [55, 20, 3, 1, 0.3, 4],  # Higher Black
    "southwest": [50, 5, 4, 3, 0.5, 5],  # Higher Native American
}

REGIONAL_ETHNICITY_WEIGHTS = {
    "east_coast": [82, 10, 3, 1, 4],  # Diverse Hispanic
    "west_coast": [65, 22, 1, 0.5, 11.5],  # High Mexican heritage
    "midwest": [90, 6, 1, 0.5, 2.5],  # Lower Hispanic
    "south": [78, 14, 1, 2, 5],  # Cuban in FL, Mexican in TX
    "southwest": [55, 32, 0.5, 0.5, 12],  # Very high Hispanic (Mexican)
}

# Global locations organized by region for geographic travel patterns
LOCATIONS_BY_REGION = {
    # US Domestic - grouped by region
    "us_east": [
        {
            "city": "New York",
            "country": "United States",
            "lat": 40.7128,
            "lng": -74.0060,
        },
        {"city": "Boston", "country": "United States", "lat": 42.3601, "lng": -71.0589},
        {
            "city": "Washington D.C.",
            "country": "United States",
            "lat": 38.9072,
            "lng": -77.0369,
        },
        {
            "city": "Philadelphia",
            "country": "United States",
            "lat": 39.9526,
            "lng": -75.1652,
        },
        {"city": "Miami", "country": "United States", "lat": 25.7617, "lng": -80.1918},
        {
            "city": "Atlanta",
            "country": "United States",
            "lat": 33.7490,
            "lng": -84.3880,
        },
    ],
    "us_west": [
        {
            "city": "Los Angeles",
            "country": "United States",
            "lat": 34.0522,
            "lng": -118.2437,
        },
        {
            "city": "San Francisco",
            "country": "United States",
            "lat": 37.7749,
            "lng": -122.4194,
        },
        {
            "city": "Seattle",
            "country": "United States",
            "lat": 47.6062,
            "lng": -122.3321,
        },
        {
            "city": "Las Vegas",
            "country": "United States",
            "lat": 36.1699,
            "lng": -115.1398,
        },
        {
            "city": "San Diego",
            "country": "United States",
            "lat": 32.7157,
            "lng": -117.1611,
        },
        {
            "city": "Portland",
            "country": "United States",
            "lat": 45.5152,
            "lng": -122.6784,
        },
    ],
    "us_central": [
        {
            "city": "Chicago",
            "country": "United States",
            "lat": 41.8781,
            "lng": -87.6298,
        },
        {
            "city": "Denver",
            "country": "United States",
            "lat": 39.7392,
            "lng": -104.9903,
        },
        {"city": "Dallas", "country": "United States", "lat": 32.7767, "lng": -96.7970},
        {
            "city": "Houston",
            "country": "United States",
            "lat": 29.7604,
            "lng": -95.3698,
        },
        {"city": "Austin", "country": "United States", "lat": 30.2672, "lng": -97.7431},
        {
            "city": "Phoenix",
            "country": "United States",
            "lat": 33.4484,
            "lng": -112.0740,
        },
        {
            "city": "Minneapolis",
            "country": "United States",
            "lat": 44.9778,
            "lng": -93.2650,
        },
    ],
    # International - grouped by common travel routes
    "europe": [
        {"city": "London", "country": "United Kingdom", "lat": 51.5074, "lng": -0.1278},
        {"city": "Paris", "country": "France", "lat": 48.8566, "lng": 2.3522},
        {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lng": 13.4050},
        {"city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lng": 4.9041},
        {"city": "Barcelona", "country": "Spain", "lat": 41.3851, "lng": 2.1734},
        {"city": "Rome", "country": "Italy", "lat": 41.9028, "lng": 12.4964},
        {"city": "Munich", "country": "Germany", "lat": 48.1351, "lng": 11.5820},
        {"city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lng": 8.5417},
        {"city": "Dublin", "country": "Ireland", "lat": 53.3498, "lng": -6.2603},
        {"city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lng": 18.0686},
        {"city": "Lisbon", "country": "Portugal", "lat": 38.7223, "lng": -9.1393},
        {"city": "Prague", "country": "Czech Republic", "lat": 50.0755, "lng": 14.4378},
    ],
    "asia_pacific": [
        {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lng": 139.6503},
        {"city": "Singapore", "country": "Singapore", "lat": 1.3521, "lng": 103.8198},
        {"city": "Hong Kong", "country": "China", "lat": 22.3193, "lng": 114.1694},
        {"city": "Shanghai", "country": "China", "lat": 31.2304, "lng": 121.4737},
        {"city": "Beijing", "country": "China", "lat": 39.9042, "lng": 116.4074},
        {"city": "Seoul", "country": "South Korea", "lat": 37.5665, "lng": 126.9780},
        {"city": "Sydney", "country": "Australia", "lat": -33.8688, "lng": 151.2093},
        {"city": "Melbourne", "country": "Australia", "lat": -37.8136, "lng": 144.9631},
        {"city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lng": 100.5018},
        {"city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lng": 121.5654},
        {"city": "Osaka", "country": "Japan", "lat": 34.6937, "lng": 135.5023},
    ],
    "south_asia": [
        {"city": "Mumbai", "country": "India", "lat": 19.0760, "lng": 72.8777},
        {"city": "Delhi", "country": "India", "lat": 28.6139, "lng": 77.2090},
        {"city": "Bangalore", "country": "India", "lat": 12.9716, "lng": 77.5946},
        {"city": "Kuala Lumpur", "country": "Malaysia", "lat": 3.1390, "lng": 101.6869},
        {"city": "Jakarta", "country": "Indonesia", "lat": -6.2088, "lng": 106.8456},
        {"city": "Manila", "country": "Philippines", "lat": 14.5995, "lng": 120.9842},
    ],
    "middle_east": [
        {"city": "Dubai", "country": "UAE", "lat": 25.2048, "lng": 55.2708},
        {"city": "Abu Dhabi", "country": "UAE", "lat": 24.4539, "lng": 54.3773},
        {"city": "Tel Aviv", "country": "Israel", "lat": 32.0853, "lng": 34.7818},
        {"city": "Istanbul", "country": "Turkey", "lat": 41.0082, "lng": 28.9784},
        {"city": "Doha", "country": "Qatar", "lat": 25.2854, "lng": 51.5310},
    ],
    "africa": [
        {"city": "Cairo", "country": "Egypt", "lat": 30.0444, "lng": 31.2357},
        {
            "city": "Johannesburg",
            "country": "South Africa",
            "lat": -26.2041,
            "lng": 28.0473,
        },
        {
            "city": "Cape Town",
            "country": "South Africa",
            "lat": -33.9249,
            "lng": 18.4241,
        },
        {"city": "Nairobi", "country": "Kenya", "lat": -1.2921, "lng": 36.8219},
        {"city": "Lagos", "country": "Nigeria", "lat": 6.5244, "lng": 3.3792},
    ],
    "americas": [
        {"city": "Toronto", "country": "Canada", "lat": 43.6532, "lng": -79.3832},
        {"city": "Vancouver", "country": "Canada", "lat": 49.2827, "lng": -123.1207},
        {"city": "Montreal", "country": "Canada", "lat": 45.5017, "lng": -73.5673},
        {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lng": -99.1332},
        {"city": "Cancun", "country": "Mexico", "lat": 21.1619, "lng": -86.8515},
        {"city": "São Paulo", "country": "Brazil", "lat": -23.5505, "lng": -46.6333},
        {
            "city": "Rio de Janeiro",
            "country": "Brazil",
            "lat": -22.9068,
            "lng": -43.1729,
        },
        {
            "city": "Buenos Aires",
            "country": "Argentina",
            "lat": -34.6037,
            "lng": -58.3816,
        },
        {"city": "Lima", "country": "Peru", "lat": -12.0464, "lng": -77.0428},
        {"city": "Bogotá", "country": "Colombia", "lat": 4.7110, "lng": -74.0721},
    ],
}

# Travel preferences by home region (what destinations they're likely to visit)
TRAVEL_PATTERNS = {
    "east_coast": {
        # East coast residents: Europe is close, domestic East, then West
        "primary": ["us_east", "europe", "americas"],
        "secondary": ["us_central", "middle_east"],
        "rare": ["asia_pacific", "us_west", "south_asia", "africa"],
        "weights": {"primary": 60, "secondary": 25, "rare": 15},
    },
    "west_coast": {
        # West coast: Asia-Pacific is close, domestic West, then Americas
        "primary": ["us_west", "asia_pacific", "americas"],
        "secondary": ["us_central", "south_asia"],
        "rare": ["europe", "us_east", "middle_east", "africa"],
        "weights": {"primary": 60, "secondary": 25, "rare": 15},
    },
    "midwest": {
        # Midwest: Mix of both coasts, domestic Central
        "primary": ["us_central", "us_east", "americas"],
        "secondary": ["europe", "us_west"],
        "rare": ["asia_pacific", "middle_east", "south_asia", "africa"],
        "weights": {"primary": 55, "secondary": 30, "rare": 15},
    },
    "south": {
        # South: Americas (Mexico, Caribbean close), domestic, then Europe
        "primary": ["us_central", "americas", "us_east"],
        "secondary": ["europe", "us_west"],
        "rare": ["asia_pacific", "middle_east", "south_asia", "africa"],
        "weights": {"primary": 55, "secondary": 30, "rare": 15},
    },
    "southwest": {
        # Southwest: West coast nearby, Americas (Mexico close)
        "primary": ["us_west", "us_central", "americas"],
        "secondary": ["asia_pacific", "europe"],
        "rare": ["us_east", "middle_east", "south_asia", "africa"],
        "weights": {"primary": 55, "secondary": 30, "rare": 15},
    },
}

# Operating systems with realistic market share distribution
OPERATING_SYSTEMS = [
    {"os": "Windows 11", "version": "23H2", "type": "desktop"},
    {"os": "Windows 10", "version": "22H2", "type": "desktop"},
    {"os": "macOS", "version": "Sonoma 14.2", "type": "desktop"},
    {"os": "macOS", "version": "Ventura 13.6", "type": "desktop"},
    {"os": "iOS", "version": "17.2", "type": "mobile"},
    {"os": "iOS", "version": "16.7", "type": "mobile"},
    {"os": "Android", "version": "14", "type": "mobile"},
    {"os": "Android", "version": "13", "type": "mobile"},
    {"os": "Linux", "version": "Ubuntu 22.04", "type": "desktop"},
    {"os": "ChromeOS", "version": "120", "type": "desktop"},
]
OS_WEIGHTS = [20, 15, 12, 5, 15, 5, 12, 8, 5, 3]

# Regional OS preferences (West coast more Mac, etc.)
REGIONAL_OS_WEIGHTS = {
    "west_coast": [15, 12, 18, 8, 18, 6, 10, 6, 4, 3],  # More Mac/iOS
    "east_coast": [18, 14, 14, 6, 16, 5, 12, 8, 4, 3],  # Balanced
    "midwest": [22, 18, 10, 4, 14, 5, 12, 8, 4, 3],  # More Windows
    "south": [20, 16, 12, 5, 15, 5, 12, 8, 4, 3],  # Balanced
    "southwest": [18, 14, 14, 6, 16, 6, 12, 7, 4, 3],  # Balanced
}


def get_generation(birth_year):
    """
    Determine generation cohort from birth year.

    Generation cohorts:
    - Silent Generation: Pre-1946
    - Baby Boomer: 1946-1964
    - Gen X: 1965-1980
    - Millennial: 1981-1996
    - Gen Z: 1997-2012
    - Gen Alpha: 2013-2025
    """
    if birth_year < 1946:
        return "Silent"
    elif birth_year <= 1964:
        return "Baby Boomer"
    elif birth_year <= 1980:
        return "Gen X"
    elif birth_year <= 1996:
        return "Millennial"
    elif birth_year <= 2012:
        return "Gen Z"
    else:
        return "Gen Alpha"


def generate_dob_for_age_group(age_min, age_max):
    """Generate DOB with more realistic date variance"""
    age = random.randint(age_min, age_max)
    birth_year = 2024 - age
    # More realistic month distribution
    month = random.randint(1, 12)
    # Random day (avoiding 29-31 for simplicity)
    day = random.randint(1, 28)
    generation = get_generation(birth_year)
    return f"{birth_year}-{month:02d}-{day:02d}", age, generation


def generate_marital_status(age_group):
    """Generate marital status based on age group (realistic distribution)"""
    marital_weights = MARITAL_BY_AGE.get(age_group, MARITAL_BY_AGE[(35, 44)])
    statuses = list(marital_weights.keys())
    weights = list(marital_weights.values())
    return random.choices(statuses, weights=weights)[0]


def generate_income(marital_status, age):
    """Generate income based on marital status and age"""
    # Select income table based on marital status
    if marital_status in ["Married", "Domestic Partnership"]:
        incomes = INCOME_MARRIED
        weights = INCOME_MARRIED_WEIGHTS.copy()
    elif marital_status in ["Divorced", "Separated"]:
        incomes = INCOME_DIVORCED
        weights = INCOME_DIVORCED_WEIGHTS.copy()
    elif marital_status == "Widowed":
        incomes = INCOME_WIDOWED
        weights = INCOME_WIDOWED_WEIGHTS.copy()
    else:  # Single
        incomes = INCOME_SINGLE
        weights = INCOME_SINGLE_WEIGHTS.copy()

    # Age-based income adjustments
    # Younger people (18-24) earn less, peak earning years (45-54)
    if age < 25:
        # Shift weights toward lower incomes
        weights = [
            w * 1.5 if i < len(weights) // 2 else w * 0.5 for i, w in enumerate(weights)
        ]
    elif age < 35:
        # Slightly lower than peak
        weights = [
            w * 1.2 if i < len(weights) // 2 else w * 0.9 for i, w in enumerate(weights)
        ]
    elif 45 <= age <= 54:
        # Peak earning years - shift toward higher incomes
        weights = [
            w * 0.8 if i < len(weights) // 2 else w * 1.3 for i, w in enumerate(weights)
        ]
    elif age >= 65:
        # Retirement - often reduced income, more fixed
        weights = [
            w * 1.3 if i < len(weights) // 2 else w * 0.7 for i, w in enumerate(weights)
        ]

    # Normalize weights
    total = sum(weights)
    weights = [w / total * 100 for w in weights]

    return random.choices(incomes, weights=weights)[0]


def generate_race_ethnicity(home_region):
    """Generate race and ethnicity based on regional demographics"""
    # Use regional weights for more realistic geographic distribution
    race_weights = REGIONAL_RACE_WEIGHTS.get(home_region, RACE_WEIGHTS)
    ethnicity_weights = REGIONAL_ETHNICITY_WEIGHTS.get(home_region, ETHNICITY_WEIGHTS)

    race = random.choices(RACES, weights=race_weights)[0]
    ethnicity = random.choices(ETHNICITIES, weights=ethnicity_weights)[0]

    return race, ethnicity


def generate_location_history(home_region, num_locations=None):
    """Generate geographically realistic location history based on home region"""
    if num_locations is None:
        # Most people have 1-5 locations, frequent travelers have more
        num_locations = random.choices(
            [1, 2, 3, 4, 5, 6, 8, 10, 12, 15],
            weights=[15, 20, 20, 15, 12, 8, 5, 3, 1, 1],
        )[0]

    # Get travel patterns for this home region
    patterns = TRAVEL_PATTERNS.get(home_region, TRAVEL_PATTERNS["midwest"])

    # Build weighted list of destination regions
    selected_locations = []

    for _ in range(num_locations):
        # Determine which tier of destinations to pick from
        tier_roll = random.randint(1, 100)
        if tier_roll <= patterns["weights"]["primary"]:
            region_pool = patterns["primary"]
        elif (
            tier_roll
            <= patterns["weights"]["primary"] + patterns["weights"]["secondary"]
        ):
            region_pool = patterns["secondary"]
        else:
            region_pool = patterns["rare"]

        # Pick a random region from the tier
        chosen_region = random.choice(region_pool)

        # Pick a random location from that region
        region_locations = LOCATIONS_BY_REGION.get(chosen_region, [])
        if region_locations:
            loc = random.choice(region_locations)
            # Avoid duplicates
            if loc not in selected_locations:
                selected_locations.append(loc)

    # Generate visit details
    history = []
    base_year = 2024

    for loc in selected_locations:
        years_ago = random.randint(0, 3)
        month = random.randint(1, 12)
        day = random.randint(1, 28)

        # Determine visit type based on destination
        if loc["country"] == "United States":
            visit_type = random.choices(
                ["business", "leisure", "family", "transit"], weights=[30, 40, 25, 5]
            )[0]
            duration = random.randint(1, 7)  # Domestic trips shorter
        else:
            visit_type = random.choices(
                ["business", "leisure", "transit", "relocation"],
                weights=[25, 55, 15, 5],
            )[0]
            duration = random.randint(3, 21)  # International trips longer

        visit = {
            "city": loc["city"],
            "country": loc["country"],
            "coordinates": {"lat": loc["lat"], "lng": loc["lng"]},
            "visited_date": f"{base_year - years_ago}-{month:02d}-{day:02d}",
            "duration_days": duration,
            "visit_type": visit_type,
        }
        history.append(visit)

    # Sort by date (most recent first)
    history.sort(key=lambda x: x["visited_date"], reverse=True)

    return history


def generate_ip_address(home_city_data):
    """Generate IP address realistic for the user's home region"""
    # Use region-specific IP ranges
    ip_ranges = home_city_data.get("ip_ranges", [(64, 128)])

    # Pick a range and generate IP
    chosen_range = random.choice(ip_ranges)
    first_octet = random.randint(chosen_range[0], chosen_range[1])

    return f"{first_octet}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"


def generate_device_info(home_region):
    """Generate device/OS information with regional preferences"""
    # Use regional OS weights if available
    weights = REGIONAL_OS_WEIGHTS.get(home_region, OS_WEIGHTS)
    os_info = random.choices(OPERATING_SYSTEMS, weights=weights)[0]

    return {
        "os_name": os_info["os"],
        "os_version": os_info["version"],
        "device_type": os_info["type"],
    }


# Build weighted list of home cities
home_cities = list(LOCATION_POOLS.keys())
home_weights = [LOCATION_POOLS[city]["weight"] for city in home_cities]

with open("fixtures/customers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(
        [
            "name",
            "email",
            "phone",
            "ssn",
            "address",
            "city",
            "state",
            "zip",
            "dob",
            "age",
            "generation",
            "gender",
            "race",
            "ethnicity",
            "marital_status",
            "income",
            "location_history",
            "ip_address",
            "os_name",
            "os_version",
            "device_type",
        ]
    )

    for i in range(num_records):
        # Select home city with geographic data
        home_city = random.choices(home_cities, weights=home_weights)[0]
        city_data = LOCATION_POOLS[home_city]

        state = city_data["state"]
        zip_code = city_data["zip"]
        home_region = city_data["region"]

        # Generate age and DOB
        age_group = random.choices(AGE_GROUPS, weights=AGE_WEIGHTS, k=1)[0]
        dob, age, generation = generate_dob_for_age_group(age_group[0], age_group[1])

        gender = random.choices(GENDERS, weights=GENDER_WEIGHTS)[0]

        # Generate race and ethnicity based on regional demographics
        race, ethnicity = generate_race_ethnicity(home_region)

        # Generate marital status based on age (realistic correlation)
        marital_status = generate_marital_status(age_group)

        # Generate income based on marital status and age
        income = generate_income(marital_status, age)

        # Generate geographically realistic data based on home location
        location_history = generate_location_history(home_region)
        ip_address = generate_ip_address(city_data)
        device_info = generate_device_info(home_region)

        writer.writerow(
            [
                fake.name(),
                fake.email(),
                fake.phone_number(),
                fake.ssn(),
                fake.street_address(),
                home_city,
                state,
                zip_code,
                dob,
                age,
                generation,
                gender,
                race,
                ethnicity,
                marital_status,
                income,
                json.dumps(location_history),  # Store as JSON string
                ip_address,
                device_info["os_name"],
                device_info["os_version"],
                device_info["device_type"],
            ]
        )

print(f"Generated {num_records} records with realistic, correlated data")
print(f"\nFields generated (21 total):")
print(f"  Personal: name, email, phone, ssn, address, city, state, zip")
print(
    f"  Demographics: dob, age, generation, gender, race, ethnicity, marital_status, income"
)
print(f"  Location History: Global travel patterns based on home region")
print(f"  Device Data: ip_address, os_name, os_version, device_type")
print(f"\nRealistic correlations:")
print(f"  - Generation cohorts derived from DOB:")
print(f"      Silent (Pre-1946) | Baby Boomer (1946-1964) | Gen X (1965-1980)")
print(f"      Millennial (1981-1996) | Gen Z (1997-2012) | Gen Alpha (2013-2025)")
print(f"  - Age groups: 18-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75-85, 86-95")
print(f"  - Marital status: Age-correlated (young=mostly single, older=more widowed)")
print(f"  - Income: Based on marital status + age")
print(f"      Single: $25k-$180k | Married: $45k-$350k (dual income)")
print(f"      Divorced: $30k-$200k | Widowed: $22k-$180k (often fixed)")
print(f"  - Race/Ethnicity: Regional variations based on US Census data")
print(f"      West Coast: Higher Asian/Pacific Islander")
print(f"      South: Higher Black/African American")
print(f"      Southwest: Higher Hispanic/Latino, Native American")
print(f"  - Geography: Travel patterns based on home region")
print(f"      East Coast → Europe, Eastern US")
print(f"      West Coast → Asia-Pacific, Western US")
print(f"  - IP addresses: Correlated to home region ISP ranges")
print(f"  - OS preferences: Regional variations (West coast = more Mac/iOS)")
