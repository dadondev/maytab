import phonenumbers


def valid_phone(number: str | None) -> bool:
    if not isinstance(number, str):
        return False

    try:
        raw = number.strip()
        if not raw:
            return False
        if not raw.startswith("+"):
            raw = "+998" + raw.lstrip("998").lstrip("+")

        parsed_number = phonenumbers.parse(raw, "UZ")
        return phonenumbers.is_valid_number_for_region(parsed_number, "UZ")
    except Exception:
        return False
