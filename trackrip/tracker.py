"""
A module for identifying and representing different tracker formats, and the
samples inside them.
"""
from io import SEEK_CUR
from . import pcm

def identify_module(file) -> str:
    """
    Determines the format of the module file provided and returns it as an
    appropriate object.
    """
    magic = file.read(8)
    if magic[:4] == b"IMPM":
        return ImpulseTrackerIT(file)
    if magic[:8] == b"ziRCONia":
        raise NotImplementedError("MMCMP-compression isn't supported.")
    if magic[:4] == b"\xc1\x83*\x9e":
        raise NotImplementedError("UMX files aren't supported yet.")

    file.seek(28)
    sig_one = file.read(2)
    file.seek(44)
    sig_two = file.read(4)
    if sig_one == b"\x1A\x10" and sig_two == b'SCRM':
        return ScreamTracker3S3M(file)

    return ProtrackerMOD(file)

class ProtrackerMOD:
    """Retrieves sample data from Protracker MOD files."""

    # Amiga Paula clock rate closest to 8372Hz C
    SAMPLE_RATE = 8363
    SAMPLE_WIDTH = 8 // 8

    def __init__(self, file):
        self.file = file

        self.file.seek(1080)
        self.identifier = self.file.read(4)

        self.file.seek(0)
        self.title = self.file.read(20).decode("ascii")

        self.samples = []
        for _ in range(self.get_sample_count()):
            sample = self.decode_sample_header(self.file.read(30))
            self.samples.append(sample)

        self.file.seek(1, SEEK_CUR) # skip number of song positions
        self.file.seek(1, SEEK_CUR) # this byte can be ignored

        pattern_count = self.find_highest_pattern(self.file.read(128))

        self.file.seek(4, SEEK_CUR) # we've already got the identifier

        for _ in range(pattern_count + 1): # skip pattern data
            self.file.seek(256 * self.get_channel_count(), SEEK_CUR)

        for i, sample in enumerate(self.samples):
            sample["number"] = i
            if sample["length"] > 0:
                sample["rate"] = self.SAMPLE_RATE
                sample["width"] = self.SAMPLE_WIDTH
                sample["data"] = self.file.read(sample["length"])
                sample["data"] = pcm.signed_to_unsigned(sample["data"])

    def get_sample_count(self) -> int:
        """Returns the # of samples present."""
        has_alpha = []
        for char in self.identifier:
            has_alpha.append(bytes([char]).isalpha())
        if any(has_alpha):
            return 31
        return 15

    def get_channel_count(self) -> int:
        """Returns the # of channels present."""
        number_of_channels = 4
        if self.identifier in [b"M.K.", b"M!K!", b"FLT4"]:
            number_of_channels = 4
        elif self.identifier in [b"6CHN"]:
            number_of_channels = 6
        elif self.identifier in [b"8CHN", b"CD81", b"OKTA", b"OCTA", b"FLT8"]:
            number_of_channels = 8
        elif self.identifier in [b"2CHN"]:
            number_of_channels = 2
        return number_of_channels

    @staticmethod
    def decode_sample_header(header_bytes) -> dict:
        """Returns a dict of the sample's header data decoded from header_bytes."""
        assert len(header_bytes) == 30, "Sample header should be 30 bytes."

        sample = {}

        sample["name"] = header_bytes[:22].decode("ascii")
        sample["length"] = int.from_bytes(header_bytes[22:24], "big") * 2

        return sample

    @staticmethod
    def find_highest_pattern(pattern_table_bytes) -> int:
        """Returns the highest pattern in pattern_table_bytes."""
        last_pattern = 0
        for i in range(128):
            pattern = pattern_table_bytes[i]
            if pattern > last_pattern:
                last_pattern = pattern
        return last_pattern

class ScreamTracker3S3M:
    """Retrieves sample data from ScreamTracker 3 S3M files."""

    SAMPLE_WIDTH = 8 // 8

    def __init__(self, file):
        self.file = file

        self.file.seek(0)
        self.title = self.file.read(28).decode("ascii")

        # skip sig1, type & reserved
        self.file.seek(4, SEEK_CUR)

        order_count = int.from_bytes(self.file.read(2), "little")
        instrument_count = int.from_bytes(self.file.read(2), "little")

        # skip patternPtrCount, flags, trackVersion
        self.file.seek(6, SEEK_CUR)

        sample_type = int.from_bytes(self.file.read(2), "little")
        signed = bool(sample_type == 1)

        # skip sig2, globalVolume, initialSpeed, initialTempo, masterVolume,
        # ultraClickRemoval, defaultPan, reserved, ptrSpecial, channelSettings
        self.file.seek(52, SEEK_CUR)
        # skip orderList
        self.file.seek(order_count, SEEK_CUR)

        instrument_pointers = []
        for _ in range(instrument_count):
            # convert parapointer
            pointer = int.from_bytes(self.file.read(2), "little") * 16
            instrument_pointers.append(pointer)

        self.samples = []
        for i, pointer in enumerate(instrument_pointers):
            self.file.seek(pointer)
            if self.file.read(1) == b"\x01": # PCM instrument
                self.file.seek(-1, SEEK_CUR)
                sample = self.decode_sample_header(self.file.read(80))
                sample["number"] = i
                self.samples.append(sample)

        for sample in self.samples:
            self.file.seek(sample["pointer"])
            if sample["length"] > 0:
                sample["data"] = self.file.read(sample["length"])
                if signed:
                    sample["data"] = pcm.signed_to_unsigned(sample["data"])

    @staticmethod
    def decode_sample_header(header_bytes) -> dict:
        """Returns a dict of the sample's header data decoded from header_bytes."""
        assert len(header_bytes) == 80, "Sample header should be 80 bytes."
        assert header_bytes[76:80] == b"SCRS", "Sample header should end with \"SCRS\"."

        sample = {}

        # skip DOS instrument filename

        sample_parapointer_high = int.from_bytes(header_bytes[13:14], "little")
        sample_parapointer_low = int.from_bytes(header_bytes[14:16], "little")
        # convert from 24-bit parapointer
        sample["pointer"] = (sample_parapointer_high >> 16) + sample_parapointer_low * 16

        sample["length"] = int.from_bytes(header_bytes[16:20], "little")

        sample["loop_start"] = int.from_bytes(header_bytes[20:22], "little")
        sample["loop_end"] = int.from_bytes(header_bytes[24:26], "little")

        # skip volume & unused

        pack = int.from_bytes(header_bytes[30:31], "little")
        if pack != 0:
            raise NotImplementedError("Samples packed in DP30ADPCM aren't supported.")

        flags = int.from_bytes(header_bytes[31:32], "little")
        # if loop flag is off
        if not flags & 1:
            sample["loop_start"] = None
            sample["loop_end"] = None
        if flags & 2:
            raise NotImplementedError("Stereo samples aren't supported.")
        # 16-bit sample
        if flags & 4:
            sample["width"] = 16//8
        else:
            sample["width"] = 8//8

        sample["rate"] = int.from_bytes(header_bytes[32:36], "little")

        # skip internal

        sample["name"] = header_bytes[48:76].decode("ascii")

        return sample

class ImpulseTrackerIT:
    """Retrieves sample data from Impulse Tracker IT files."""

    def __init__(self, file):
        self.file = file

        self.file.seek(4)
        self.title = self.file.read(26).decode("ascii")

        # skip pattern row highlight
        self.file.seek(2, SEEK_CUR)

        order_count = int.from_bytes(self.file.read(2), "little")
        instrument_count = int.from_bytes(self.file.read(2), "little")
        sample_count = int.from_bytes(self.file.read(2), "little")

        self.file.seek(192 + order_count + (instrument_count * 4))

        sample_header_pointers = []
        for _ in range(sample_count):
            pointer = int.from_bytes(self.file.read(4), "little")
            sample_header_pointers.append(pointer)

        self.samples = []
        for i, pointer in enumerate(sample_header_pointers):
            self.file.seek(pointer)
            sample = self.decode_sample_header(self.file.read(80))
            sample["number"] = i
            self.samples.append(sample)

        for sample in self.samples:
            if sample["length"] > 0:
                self.file.seek(sample["pointer"])
                sample_data = self.file.read(sample["length"])
                if not sample["compressed"]:
                    sample["data"] = sample_data
                else:
                    sample["data"] = self.decompress_it_sample(sample_data)
                # HACK: don't know why 8-bit samples are signed while 16-bit samples are unsigned
                if sample["width"] == 1 or not sample["signed"]:
                    sample["data"] = pcm.signed_to_unsigned(sample["data"])

    @staticmethod
    def decode_sample_header(header_bytes) -> dict:
        """Returns a dict of the sample's header data decoded from header_bytes."""
        assert len(header_bytes) == 80, "Sample header should be 80 bytes."
        assert header_bytes[:4] == b"IMPS", "Sample header should start with \"IMPS\"."

        sample = {}

        #skip DOS filename, blank and global volume

        flags = int.from_bytes(header_bytes[18:19], "big")
        # assert (flags >> 0) & 1 == 1
        # on = 16-bit, off = 8-bit
        sample["width"] = 16//8 if (flags >> 1) & 1 else 8//8
        if (flags >> 3) & 1:
            raise NotImplementedError("Stereo samples aren't supported.")
        sample["compressed"] = bool((flags >> 4) & 1)
        # skip loop flags

        # skip instrument volume

        sample["name"] = header_bytes[20:46].decode("ascii")

        # skip default pan

        convert = int.from_bytes(header_bytes[46:47], "big")
        sample["signed"] = bool(convert & 1)

        # length of sample is stored in no. of samples NOT no. of bytes
        sample["length"] = int.from_bytes(header_bytes[48:52], "little") * sample["width"]
        sample["loop_start"] = int.from_bytes(header_bytes[52:56], "little") * sample["width"]
        sample["loop_end"] = int.from_bytes(header_bytes[56:60], "little") * sample["width"]

        sample["rate"] = int.from_bytes(header_bytes[60:64], "little")

        #skip sustain loop start / end

        sample["pointer"] = int.from_bytes(header_bytes[72:76], "little")

        return sample

    @staticmethod
    def decompress_it_sample(sample_bytes) -> bytes:
        # TODO: investigate compression flag
        return sample_bytes