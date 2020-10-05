from .mod import ProtrackerMOD
from .s3m import ScreamTracker3S3M
from .it import ImpulseTrackerMOD

def parse_module(file) -> str:
    """
    Determines the format of the module file provided and returns the
    appropriate object.
    """
    # if file.read(4) == b"IMPM":
    #     return "IT"

    file.seek(28)
    sig_one = file.read(2)
    file.seek(44)
    sig_two = file.read(4)
    if sig_one == b"\x1A\x10" and sig_two == b'SCRM':
        return ScreamTracker3S3M(file)

    return ProtrackerMOD(file)
