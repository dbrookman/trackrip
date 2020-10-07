def signed_to_unsigned(data):
    converted = bytearray()
    for byte in data:
        if byte > 127:
            signed = byte - 127
        else:
            signed = byte + 127
        converted.append(signed)
    return converted
