"""For modifying PCM data."""

def signed_to_unsigned(data):
    """
    Converts signed data to unsigned data
    (that's not exactly what this does but I'm not sure what to call it)
    TODO: Figure out exactly why this works.
    """
    converted = bytearray()
    for byte in data:
        if byte > 127:
            signed = byte - 127
        else:
            signed = byte + 127
        converted.append(signed)
    return converted
