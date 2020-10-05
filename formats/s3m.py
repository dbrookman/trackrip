from io import SEEK_CUR

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
