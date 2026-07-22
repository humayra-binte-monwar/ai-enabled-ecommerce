from app.schemas.product import Product

TAG_RULES = {
    "frozen": [
        "frozen",
        "kazifarms",
        "kazi",
        "chicken strips",
        "meat ball",
        "sausage",
        "nugget",
        "paratha",
        "fries",
    ],
    "ready_to_cook": [
        "chicken strips",
        "meat ball",
        "sausage",
        "nugget",
        "haleem mix",
        "readymix",
    ],
    "dairy": ["milk", "full cream", "coffee mate", "powder"],
    "breakfast": ["egg", "milk", "tea", "coffee", "oats", "bread", "atta"],
    "egg": ["egg loose"],
    "tea": ["tea", "mirzapore", "seylon"],
    "coffee": ["coffee", "nescafe", "davidoff", "coffee mate"],
    "rice": ["rice", "chinigura", "miniket", "basmati"],
    "dal": ["dal", "lentil", "moshur"],
    "oil": ["oil", "rice bran", "soyabean", "soybean", "mustard"],
    "staple": ["rice", "dal", "salt", "sugar", "atta", "flour", "oil"],
    "spice": [
        "masala",
        "powder",
        "chilli",
        "turmeric",
        "holud",
        "tejapata",
        "bay leaves",
        "oregano",
    ],
    "produce": ["onion", "piyaj", "chilli green", "kacha morich"],
    "beverage": ["7up", "drink", "juice", "orange", "tea", "coffee"],
    "snack": ["biscuit", "cake", "noodles", "chips"],
    "noodles": ["noodle", "noodles"],
    "sweetener": ["sugar", "honey"],
    "protein": ["egg", "chicken", "dal", "lentil", "milk"],
    "diabetic": ["diabetic"],
    "health": ["diabetic", "rice bran", "honey"],
    "cleaning": [
        "cleaner",
        "detergent",
        "dish wash",
        "dishwash",
        "toilet",
        "glass cleaner",
        "tiles cleaner",
        "washing bar",
    ],
    "laundry": ["detergent", "surf excel", "rin", "wheel"],
    "dishwashing": ["dish wash", "dishwash", "vim", "d-care", "scrubber"],
    "toilet_cleaner": ["toilet cleaner", "domex", "harpoon", "powerx"],
    "personal_care": [
        "shampoo",
        "body wash",
        "body spray",
        "deodorant",
        "dove",
        "lux",
        "fogg",
        "axe",
    ],
    "hair_care": ["shampoo", "hair"],
    "fragrance": ["body spray", "deodorant", "fogg", "axe", "kool", "havoc"],
    "bulk_pack": ["1kg", "2kg", "5ltr", "1000gm", "12pcs", "16pcs"],
    "value_pack": ["buy", "get", "free", "family pack"],
}

CATEGORY_BY_TAG = {
    "frozen": "Frozen Foods",
    "cleaning": "Cleaning",
    "personal_care": "Personal Care",
    "dairy": "Dairy",
    "rice": "Rice & Grains",
    "dal": "Lentils & Pulses",
    "oil": "Cooking Oil",
    "spice": "Spices",
    "produce": "Fresh Produce",
    "beverage": "Beverages",
    "snack": "Snacks",
}

PRODUCT_TYPE_BY_TAG = {
    "frozen": "frozen_food",
    "cleaning": "household_cleaning",
    "personal_care": "personal_care",
    "staple": "grocery_staple",
    "beverage": "beverage",
    "snack": "snack",
    "protein": "protein",
}


def infer_tags(product: Product) -> list[str]:
    searchable_text = " ".join(
        [
            product.name,
            product.category,
            product.brand or "",
            product.unit or "",
        ]
    ).lower()

    tags = [
        tag
        for tag, keywords in TAG_RULES.items()
        if any(keyword in searchable_text for keyword in keywords)
    ]

    return list(dict.fromkeys(tags))


def infer_normalized_category(tags: list[str], fallback: str) -> str:
    for tag, category in CATEGORY_BY_TAG.items():
        if tag in tags:
            return category

    return fallback


def infer_product_type(tags: list[str]) -> str | None:
    for tag, product_type in PRODUCT_TYPE_BY_TAG.items():
        if tag in tags:
            return product_type

    return None


def enrich_product(product: Product) -> Product:
    tags = infer_tags(product)

    return product.model_copy(
        update={
            "tags": tags,
            "normalized_category": infer_normalized_category(tags, product.category),
            "product_type": infer_product_type(tags),
        }
    )
