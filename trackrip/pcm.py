"""For modifying PCM data."""

def signed_to_unsigned_8bit(data):
    """
    Converts 8-bit signed data initally read as unsigned data back to its
    original relative position.
    """
    # Python reads bytes as unsigned chars (0 to 255).
    # For example: Byte "FF" in a signed file is -1, but Python will read it
    # as the unsigned value 255. -1 is halfway in the signed range (-127 to 127)
    # at position 127 (counting the sign bit). However, 255 corresponds to the
    # very end of the unsigned range. To match the original position as a signed
    # number, we subtract 128, landing us at the original position of 127.
    # While positive decimals will be the same signed or unsigned (under 127),
    # their relative position will change again. 127 is position 255 while
    # signed, and 127 while unsigned. We add 128 and arrive at 255, the correct
    # position.
    converted = bytearray()
    for byte in data:
        if byte > 127:
            signed = byte - 128
        else:
            signed = byte + 128
        converted.append(signed)
    return converted
