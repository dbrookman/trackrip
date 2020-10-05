import trackrip.formats as formats

def parse_module(file) -> str:
    """
    Determines the format of the module file provided and returns it as an
    appropriate object.
    """
    if file.read(4) == b"IMPM":
        return formats.ImpulseTrackerIT(file)

    file.seek(28)
    sig_one = file.read(2)
    file.seek(44)
    sig_two = file.read(4)
    if sig_one == b"\x1A\x10" and sig_two == b'SCRM':
        return formats.ScreamTracker3S3M(file)

    return formats.ProtrackerMOD(file)
