def get_addresses(latitude, longitude, result_type="political"):
    # result_typeパラメータを使用して特定の住所タイプに絞り込む
    results = gmaps.reverse_geocode((latitude, longitude), result_type=[result_type] if result_type else None)
    addresses = []
    for result in results:
        addr = result['formatted_address']
        addresses.append(addr)
    return addresses
