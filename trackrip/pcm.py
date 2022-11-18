"""For modifying PCM data."""
import struct

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

def delta_encoding_to_real_data(data, bits=8) -> bytearray:
    """Converts an array of bytes stored as delta values to real values."""
    delta_data = bytearray(len(data))
    old = 0
    if bits == 8:
        for i in range(len(data)):
            new = (data[i] + old) % 256
            delta_data[i] = new
            old = new
    elif bits == 16:
        for i in range(len(data) // 2):
            current_bytes = data[i*2:(i*2)+2]
            new = (struct.unpack("<H", current_bytes)[0] + old) % 65536
            new_split = struct.unpack("<BB", new.to_bytes(2, "little"))
            delta_data[i*2], delta_data[(i*2)+1] = new_split
            old = new
    else:
        raise NotImplementedError("Only supports 8-bit and 16-bit delta encoding.")
    return delta_data
