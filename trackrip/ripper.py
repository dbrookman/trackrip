import trackrip.tracker as tracker

def parse_module(file) -> str:
    """
    Determines the format of the module file provided and returns it as an
    appropriate object.
    """
    s = file.read(4)
    if s == b"IMPM":
        return tracker.ImpulseTrackerIT(file)
    elif s == b"\xc1\x83*\x9e":
        raise NotImplementedError("UMX files aren't supported yet.")

    file.seek(28)
    sig_one = file.read(2)
    file.seek(44)
    sig_two = file.read(4)
    if sig_one == b"\x1A\x10" and sig_two == b'SCRM':
        return tracker.ScreamTracker3S3M(file)

    return tracker.ProtrackerMOD(file)
