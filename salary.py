def predict_salary(title: str, canton: str):
    base = 70000

    title_lower = title.lower()

    if "senior" in title_lower:
        base *= 1.3
    elif "junior" in title_lower:
        base *= 0.8

    if canton == "ZH":
        base *= 1.15
    elif canton == "GE":
        base *= 1.1
    elif canton == "SG":
        base *= 1.05

    return int(base)
