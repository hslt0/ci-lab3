def validate_variant(data):
    if not isinstance(data, dict):
        raise ValueError("JSON має містити об'єкт.")

    size = data.get("field_size")
    ships = data.get("ships")
    reefs = data.get("reefs")
    if not isinstance(size, int) or size < 2:
        raise ValueError("field_size має бути цілим числом не менше 2.")
    if not isinstance(ships, list) or not ships:
        raise ValueError("ships має бути непорожнім списком довжин.")
    if any(not isinstance(length, int) or length < 1 or length > size for length in ships):
        raise ValueError("Усі довжини кораблів мають бути цілими числами в межах поля.")
    if not isinstance(reefs, list):
        raise ValueError("reefs має бути списком координат.")

    reef_set = set()
    for reef in reefs:
        if not isinstance(reef, list) or len(reef) != 2:
            raise ValueError("Кожен риф має бути масивом [row, col].")
        row, col = reef
        if (not isinstance(row, int) or not isinstance(col, int)
                or not 0 <= row < size or not 0 <= col < size):
            raise ValueError("Координати рифів виходять за межі поля.")
        reef_set.add((row, col))

    return size, ships, reef_set
