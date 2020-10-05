from io import SEEK_CUR

class ModuleFormat():
    def __init__(self, file):
        pass

class ProtrackerMOD:
    """Retrieves sample data from Protracker MOD files."""

    # Amiga Paula clock rate closest to 8372Hz C
    SAMPLE_RATE = 8363
    SAMPLE_WIDTH = 2

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
        for _ in range(pattern_count + 1): # skip pattern data
            self.file.seek(256 * self.get_channel_count(), SEEK_CUR)

        for sample in self.samples:
            if sample["length"] > 0:
                sample["rate"] = self.SAMPLE_RATE
                sample["width"] = self.SAMPLE_WIDTH
                sample["data"] = file.read(sample["length"])

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
    def decode_sample_header(sample_bytes) -> dict:
        """Returns a dictionary of the sample's header data extracted from sample_bytes."""
        assert len(sample_bytes) == 30, "Sample header should be 30 bytes."

        sample = {}

        sample["name"] = sample_bytes[:22].decode("ascii")
        sample["length"] = int.from_bytes(sample_bytes[22:24], "big") * 2

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

    SAMPLE_WIDTH = 1

    def __init__(self, file):
        self.file = file

        file.seek(0)
        self.title = self.file.read(28).decode("ascii")

        # skip sig1, type & reserved
        file.seek(4, SEEK_CUR)

        order_count = int.from_bytes(file.read(2), "little")
        instrument_count = int.from_bytes(file.read(2), "little")

        # skip patternPtrCount, flags, trackVersion
        file.seek(6, SEEK_CUR)

        sample_type = int.from_bytes(file.read(2), "little")
        if sample_type != 2:
            raise NotImplementedError("Signed samples aren't supported yet.")

        # skip sig2, globalVolume, initialSpeed, initialTempo, masterVolume,
        # ultraClickRemoval, defaultPan, reserved, ptrSpecial, channelSettings
        file.seek(52, SEEK_CUR)
        # skip orderList
        file.seek(order_count, SEEK_CUR)

        instrument_pointers = []
        for _ in range(instrument_count):
            # convert parapointer
            instrument_pointers.append(int.from_bytes(file.read(2), "little") * 16)

        self.samples = []
        for pointer in instrument_pointers:
            file.seek(pointer)
            if file.read(1) == b"\x01": # PCM instrument
                file.seek(-1, SEEK_CUR)
                sample = self.decode_sample_header(file.read(78))
                self.samples.append(sample)

        for sample in self.samples:
            file.seek(sample["pointer"])
            sample["data"] = file.read(sample["length"])
            sample["width"] = self.SAMPLE_WIDTH

    @staticmethod
    def decode_sample_header(sample_bytes) -> dict:
        """Returns a dictionary of the sample's data extracted from sample_bytes."""
        assert len(sample_bytes) == 78, "Sample data should be 78 bytes."
        sample = {}

        # skip og instrument filename

        sample_parapointer_high = int.from_bytes(sample_bytes[13:14], "little")
        sample_parapointer_low = int.from_bytes(sample_bytes[14:16], "little")
        # convert 24-bit parapointer
        sample["pointer"] = (sample_parapointer_high >> 16) + sample_parapointer_low * 16

        sample["length"] = int.from_bytes(sample_bytes[16:20], "little")

        # skip loopStart, loopEnd, volume, and reserved

        pack = int.from_bytes(sample_bytes[30:31], "little")
        if pack != 0:
            raise NotImplementedError("Samples packed in DP30ADPCM aren't supported yet.")
        flags = int.from_bytes(sample_bytes[31:32], "little")
        if flags > 1:
            raise NotImplementedError("Stereo or 16-bit little-endian samples aren't supported yet.")

        sample["rate"] = int.from_bytes(sample_bytes[32:36], "little")

        # skip internal

        sample["name"] = sample_bytes[48:76].decode("ascii")

        return sample

class ImpulseTrackerIT:
    """Retrieves sample data from Impulse Tracker IT files."""

    def __init__(self, file):
        self.file = file
        raise NotImplementedError(".IT files aren't supported yet.")