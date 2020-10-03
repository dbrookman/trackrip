class ScreamTracker3MOD:
    """Retrieves sample data from ScreamTracker 3 S3M files."""

    SAMPLE_WIDTH = 1

    def __init__(self, file):
        self.file = file
        file.seek(0)
        self.title = self.file.read(28).decode("ascii")
        # skip sig1, type & reserved
        file.read(4)
        order_count = int.from_bytes(file.read(2), "little")
        instrument_count = int.from_bytes(file.read(2), "little")
        # skip patternPtrCount, flags, trackVersion
        file.read(6)
        sample_type = int.from_bytes(file.read(2), "little")
        assert sample_type == 2, "Signed samples aren't supported yet."
        # skip sig2, globalVolume, initialSpeed, initialTempo, masterVolume,
        # ultraClickRemoval, defaultPan, reserved, ptrSpecial, channelSettings
        file.read(52)
        # skip orderList
        file.read(order_count)
        instrument_pointers = []
        for _ in range(instrument_count):
            # convert parapointer
            instrument_pointers.append(int.from_bytes(file.read(2), "little") * 16)
        self.samples = []
        for pointer in instrument_pointers:
            file.seek(pointer)
            if file.read(1) == b"\x01": # PCM instrument
                sample = self.get_sample_info(file.read(77))
                self.samples.append(sample)
        for sample in self.samples:
            file.seek(sample["pointer"])
            sample["data"] = file.read(sample["length"])
            sample["width"] = self.SAMPLE_WIDTH

    @staticmethod
    def get_sample_info(sample_bytes) -> dict:
        """Returns a dictionary of the sample's data extracted from sample_bytes."""
        sample = {}
        # skip og instrument filename
        sample_parapointer_high = int.from_bytes(sample_bytes[12:13], "little")
        sample_parapointer_low = int.from_bytes(sample_bytes[13:15], "little")
        # convert 24-bit parapointer
        sample["pointer"] = (sample_parapointer_high >> 16) + sample_parapointer_low * 16
        sample["length"] = int.from_bytes(sample_bytes[15:19], "little")
        # skip loopStart, loopEnd, volume, and reserved
        pack = int.from_bytes(sample_bytes[29:30], "little")
        assert pack == 0, "Samples packed in DP30ADPCM aren't supported yet."
        flags = int.from_bytes(sample_bytes[30:31], "little")
        assert flags <= 1, "Stereo or 16-bit little-endian samples aren't supported yet."
        sample["rate"] = int.from_bytes(sample_bytes[31:35], "little")
        # skip internal
        sample["name"] = sample_bytes[47:75].decode("ascii")
        return sample
