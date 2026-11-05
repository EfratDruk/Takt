DEFAULT_CATEGORIES = [
    {
        "name": "הדרכה",
        "description": "קליטת שחקנים חדשים, הדרכה על מקשים ושליטה, זיהוי פריטים או מוקשים ולמידה ראשונית.",
    },
    {
        "name": "מבוא לשלב",
        "description": "מסך תדרוך לפני שלב, הוראות שלב, הצגת מטרות או תצוגת מפה לפני תחילת המשחק.",
    },
    {
        "name": "משחקיות",
        "description": "מכניקות משחק, שליטה, שמע, גרפיקה, פיזיקה וביצועים כגון השהיות, זמני טעינה, הפעלה ושמירת משחק.",
    },
    {
        "name": "מערכת סיכום",
        "description": "סטטיסטיקות לאחר משחק, סקירת ניקוד, מסכי סיכום או מערכות תחקיר.",
    },
    {
        "name": "שונות",
        "description": "משוב כללי או נושאים מנהלתיים שאינם מתאימים לקטגוריות האחרות.",
    },
]


def validate_categories(categories):
    if not isinstance(categories, list) or not categories:
        raise ValueError("יש להשאיר לפחות קטגוריה אחת.")

    validated = []
    seen_names = set()
    for category in categories:
        if not isinstance(category, dict):
            raise ValueError("פרטי הקטגוריה אינם תקינים.")
        name_value = category.get("name", "")
        description_value = category.get("description", "")
        if not isinstance(name_value, str) or not isinstance(description_value, str):
            raise ValueError("שם הקטגוריה והתיאור חייבים להיות טקסט.")
        name = name_value.strip()
        description = description_value.strip()
        if not name or not description:
            raise ValueError("לכל קטגוריה יש להזין שם ותיאור.")
        normalized_name = name.casefold()
        if normalized_name in seen_names:
            raise ValueError(f"השם '{name}' מופיע ביותר מקטגוריה אחת.")
        seen_names.add(normalized_name)
        validated.append({"name": name, "description": description})
    return validated
