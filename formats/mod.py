class ProtrackerMOD:
    """Retrieves sample data from Protracker MOD files."""

    # Amiga Paula clock rate closest to 8372Hz C
    SAMPLE_RATE = 8363

    def __init__(self, file):
        self.file = file
        self.file.seek(1080)
        self.identifier = self.file.read(4)
        self.file.seek(0)
        self.title = self.file.read(20).decode("ascii")
        print("TITLE: " + self.title)
        self.samples = []
        for i in range(self.get_sample_count()):
            sample_bytes = self.file.read(30)
            sample = self.get_sample_data(sample_bytes)
            self.samples.append(sample)
        self.file.read(1) # number of song positions
        self.file.read(1) # this byte can be ignored
        pattern_count = self.get_last_pattern(self.file.read(128))
        for i in range(pattern_count + 1): # skip pattern data
            self.file.read(256 * self.get_channel_count())
        for i, _ in enumerate(self.samples):
            sample = self.samples[i]
            if sample["length"] > 0:
                self.samples[i]["rate"] = self.SAMPLE_RATE
                self.samples[i]["data"] = file.read(sample["length"])

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
    def get_sample_data(sample_bytes) -> dict:
        """Returns a dictionary of the sample's data extracted from sample_bytes."""
        assert len(sample_bytes) == 30, "Sample data should be 30 bytes."
        sample = {}
        sample["name"] = sample_bytes[:22].strip(b"\x00\x0e").decode("ascii").strip()
        sample["length"] = int.from_bytes(sample_bytes[22:24], "big") * 2
        finetune_value = int.from_bytes(sample_bytes[24:25], "big") & 0x0F
        # convert from base-16 to a signed nibble (-8..7)
        if finetune_value > 7:
            sample["finetune"] = finetune_value - 16
        else:
            sample["finetune"] = finetune_value
        sample["volume"] = int.from_bytes(sample_bytes[25:26], "big")
        sample["loop_offset"] = int.from_bytes(sample_bytes[26:28], "big")
        sample["loop_length"] = int.from_bytes(sample_bytes[28:30], "big")
        return sample

    @staticmethod
    def get_last_pattern(pattern_table_bytes) -> int:
        """Returns the highest pattern in pattern_table_bytes."""
        last_pattern = 0
        for i in range(128):
            pattern = pattern_table_bytes[i]
            if pattern > last_pattern:
                last_pattern = pattern
        return last_pattern
