"""For modifying PCM data."""

def signed_to_unsigned(data):
    # TODO: Figure out exactly why this works.
    """Converts signed data to unsigned data"""
    converted = bytearray()
    for byte in data:
        if byte > 127:
            signed = byte - 127
        else:
            signed = byte + 127
        converted.append(signed)
    return converted
