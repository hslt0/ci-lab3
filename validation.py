def validate_variant(data):
    if not isinstance(data, dict):
        raise ValueError("JSON має містити об'єкт.")

    size = data.get("field_size")
    ships = data.get("ships")
    reefs = data.get("reefs")
    if isinstance(size, bool) or not isinstance(size, int) or size < 2:
        raise ValueError("field_size має бути цілим числом не менше 2.")
    if not isinstance(ships, list) or not ships:
        raise ValueError("ships має бути непорожнім списком довжин.")
    if any(isinstance(length, bool) or not isinstance(length, int) or length < 1 or length > size for length in ships):
        raise ValueError("Усі довжини кораблів мають бути цілими числами в межах поля.")
    if not isinstance(reefs, list):
        raise ValueError("reefs має бути списком координат.")

    reef_set = set()
    for reef in reefs:
        if not isinstance(reef, list) or len(reef) != 2:
            raise ValueError("Кожен риф має бути масивом [x, y].")
        x, y = reef
        if (isinstance(x, bool) or isinstance(y, bool)
                or not isinstance(x, int) or not isinstance(y, int)
                or not 0 <= x < size or not 0 <= y < size):
            raise ValueError("Координати рифів виходять за межі поля.")
        if (x, y) in reef_set:
            raise ValueError("Рифи не можуть повторюватися: дублікат координат [x, y].")
        reef_set.add((x, y))

    return size, ships, reef_set
