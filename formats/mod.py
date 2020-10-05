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
