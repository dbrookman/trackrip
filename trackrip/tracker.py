"""
A module for identifying and representing different tracker formats, and the
samples inside them.
"""
from enum import Enum
from io import SEEK_CUR, BytesIO

from . import pcm

class LoopType(Enum):
    """Enumerate types of sample looping."""
    OFF = 0
    FORWARD = 1
    PING_PONG = 2

def identify_module(file) -> str:
    """
    Determines the format of the module file provided and returns it as an
    appropriate object.
    """
    magic = file.read(17)
    if magic[:4] == b"IMPM":
        return ImpulseTrackerIT(file)
    if magic[:8] == b"ziRCONia":
        raise NotImplementedError("MMCMP-compression isn't supported.")
    if magic[:4] == b"\xc1\x83*\x9e":
        return UnrealEngineUMX(file)
    if magic[:17] == b"Extended Module: ":
        return FastTracker2XM(file)

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
        try:
            self.title = self.file.read(20).decode("ascii")
        # BUG: many files' first 20 bytes are ASCII, we need a better failsafe
        except UnicodeDecodeError as error:
            # can't get an ASCII title? not a mod file
            raise TypeError("File is not a tracker module.") from error

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
                sample["data"] = pcm.signed_to_unsigned_8bit(sample["data"])

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
        sample["loop_start"] = int.from_bytes(header_bytes[26:28], "big")
        sample["loop_end"] = sample["loop_start"] + int.from_bytes(header_bytes[28:30], "big")
        if sample["loop_start"] and sample["loop_end"]:
            sample["loop_type"] = LoopType.FORWARD
            if sample["loop_end"] == 1:
                sample["loop_start"] = 0
                sample["loop_end"] = 0
            else:
                # convert from words to bytes
                sample["loop_start"] *= 2
                sample["loop_end"] *= 2
        else:
            sample["loop_type"] = LoopType.OFF

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
                    sample["data"] = pcm.signed_to_unsigned_8bit(sample["data"])

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
            sample["loop_type"] = LoopType.OFF
        else:
            sample["loop_type"] = LoopType.FORWARD
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
                # python's wave module always outputs 8-bit samples as unsigned,
                # and 16-bit samples as signed.
                if sample["signed"] and sample["width"] == 1:
                    sample["data"] = pcm.signed_to_unsigned_8bit(sample["data"])
                elif not sample["signed"] and sample["width"] == 2:
                    raise NotImplementedError("Unsigned 16-bit samples aren't supported yet.")

    @staticmethod
    def decode_sample_header(header_bytes) -> dict:
        """Returns a dict of the sample's header data decoded from header_bytes."""
        assert len(header_bytes) == 80, "Sample header should be 80 bytes."
        assert header_bytes[:4] == b"IMPS", "Sample header should start with \"IMPS\"."

        sample = {}

        #skip DOS filename, blank and global volume

        flags = int.from_bytes(header_bytes[18:19], "big")

        # on = 16-bit, off = 8-bit
        sample["width"] = 16//8 if bool(flags & 0b00000010) else 8//8
        stereo_flag = bool(flags & 0b00000100)
        if stereo_flag:
            raise NotImplementedError("Stereo samples aren't supported.")
        sample["compressed"] = bool(flags & 0b00001000)
        loop_flag = bool(flags & 0b00010000)
        ping_pong_flag = bool(flags & 0b00100000)
        if loop_flag:
            if ping_pong_flag:
                sample["loop_type"] = LoopType.PING_PONG
            else:
                sample["loop_type"] = LoopType.FORWARD
        else:
            sample["loop_type"] = LoopType.OFF

        # skip instrument volume

        sample["name"] = header_bytes[20:46].decode("ascii")

        # skip default pan

        convert = int.from_bytes(header_bytes[46:47], "little")
        sample["signed"] = bool(convert & 0b00000001)

        # length of sample is stored in no. of samples NOT no. of bytes
        sample["length"] = int.from_bytes(header_bytes[48:52], "little") * sample["width"]
        sample["loop_start"] = int.from_bytes(header_bytes[52:56], "little")
        sample["loop_end"] = int.from_bytes(header_bytes[56:60], "little")

        sample["rate"] = int.from_bytes(header_bytes[60:64], "little")

        # skip sustain loop start / end

        sample["pointer"] = int.from_bytes(header_bytes[72:76], "little")

        return sample

    @staticmethod
    def decompress_it_sample(sample_bytes) -> bytes:
        raise NotImplementedError("IT214 sample compression isn't supported yet.")

class FastTracker2XM:
    """Retrieves sample data from FastTracker 2 XM files."""

    def __init__(self, file):
            self.file = file

            self.file.seek(17)
            self.title = self.file.read(20).decode("ascii")
            print(self.title)

            # skip 0x1A & tracker name
            self.file.seek(21, SEEK_CUR)

            version = list(file.read(2))
            # older versions of the XM format below $0104 could break things
            version_major = version[1]
            version_minor = version[0]
            old_version_error = "XM files under version $0104 aren't supported."
            if version_major < 1:
                raise NotImplementedError(old_version_error)
            else:
                if version_minor < 4:
                    raise NotImplementedError(old_version_error)

            # this doesn't include the previous bytes, so we add 60 for them
            xm_header_size = int.from_bytes(self.file.read(4), "little") + 60

            # size of the pattern order table in bytes
            song_length = int.from_bytes(self.file.read(2), "little")
            if song_length < 1 or song_length > 256:
                raise ValueError("XM files must have a length between 1-256.")

            # skip restart position
            self.file.seek(2, SEEK_CUR)

            channel_count = int.from_bytes(self.file.read(2), "little")
            pattern_count = int.from_bytes(self.file.read(2), "little")
            instrument_count = int.from_bytes(self.file.read(2), "little")
            frequency_table_flag = int.from_bytes(self.file.read(2), "little")

            # class FrequencyTable(Enum):
            #     """Enumerate Frequency Tables."""
            #     AMIGA = 0
            #     LINEAR = 1

            # if bool(frequency_table_flag & 0b00000001):
            #     frequency_table = FrequencyTable.LINEAR
            # else:
            #     frequency_table = FrequencyTable.AMIGA

            # if frequency_table is FrequencyTable.AMIGA:
            #     raise NotImplementedError("Amiga frequency table is not yet supported.")

            # skip flags, tempo, bpm, pattern order table & any weird extra data
            # jump directly to the first pattern header
            self.file.seek(xm_header_size)

            for i in range(pattern_count):
                pattern_header_size = int.from_bytes(self.file.read(4), "little")

                # skip packing type & rows per pattern
                self.file.seek(3, SEEK_CUR)

                pattern_data_size = int.from_bytes(self.file.read(2), "little")
                self.file.seek(pattern_data_size, SEEK_CUR)

                # skip any extra data that's left over in the pattern header
                # past the regular 9 bytes
                if pattern_data_size > 9:
                    self.file.seek(pattern_header_size - 9, SEEK_CUR)

            self.samples = []

            for i in range(instrument_count):
                instrument_header_size = int.from_bytes(self.file.read(4), "little")
                # skip instrument type & name
                self.file.seek(23, SEEK_CUR)
                instrument_sample_count = int.from_bytes(self.file.read(2), "little")

                # skip any extra data that's left over in the instrument header
                # past the regular 29 bytes.
                # none of the extra header features can be matched to anything
                # in a WAVE "smpl" chunk, so we can just skip it all.
                if instrument_header_size > 29:
                    self.file.seek(instrument_header_size - 29, SEEK_CUR)

                if instrument_sample_count > 0:
                    instrument_samples = []

                    for sample in range(instrument_sample_count):
                        sample = {}

                        sample["length"] = int.from_bytes(self.file.read(4), "little")
                        sample["loop_start"] = int.from_bytes(self.file.read(4), "little")
                        loop_length = int.from_bytes(self.file.read(4), "little")
                        sample["loop_end"] = sample["loop_start"] + loop_length
                        # skip volume
                        self.file.seek(1, SEEK_CUR)
                        fine_tune = int.from_bytes(self.file.read(1), "little", signed=True)
                        type_flag = int.from_bytes(self.file.read(1), "little")
                        if bool(type_flag & 0b00000001):
                            sample["loop_type"] = LoopType.FORWARD
                        elif bool(type_flag & 0b00000010):
                            sample["loop_type"] = LoopType.PING_PONG
                        else:
                            sample["loop_type"] = LoopType.OFF
                        sample["width"] = 16//8 if bool(type_flag & 0b00010000) else 8//8
                        if sample["width"] == 16//8:
                            sample["loop_start"] //= 2
                            sample["loop_end"] //= 2

                        # skip pan
                        self.file.seek(1, SEEK_CUR)
                        relative_note = int.from_bytes(self.file.read(1), "little", signed=True)
                        # skip reserved (ADPCM compression flag?)
                        self.file.seek(1, SEEK_CUR)
                        sample["name"] = self.file.read(22).decode("ascii")
                        instrument_samples.append(sample)

                        # C-4 is the default
                        pattern_note = 48 # C-4
                        real_note = pattern_note + relative_note

                        # FIX: Add actual Amiga frequency table interpolation
                        period = 7680 - (real_note * 64) - (fine_tune / 2)
                        frequency = 8363 * 2**((4608 - period) / 768)
                        sample["rate"] = int(frequency)

                    for sample in instrument_samples:
                        sample["data"] = self.file.read(sample["length"])

                        if sample["width"] == 8//8:
                            sample["data"] = pcm.decode_delta_encoding_8bit(sample["data"])
                            sample["data"] = pcm.signed_to_unsigned_8bit(sample["data"])
                        elif sample["width"] == 16//8:
                            sample["data"] = pcm.decode_delta_encoding_16bit(sample["data"])
                        self.samples.append(sample)

            for i in range(len(self.samples)):
                self.samples[i]["number"] = i

class UnrealEngineUMX:
    """Retrieves module file contained within an Unreal Engine UMX package file."""

    def __init__(self, file):
        self.file = file

        self.file.seek(4)
        version = int.from_bytes(file.read(4), "little")
        if version < 61:
            raise NotImplementedError("UMX files under version 61 aren't supported.")
        self.file.seek(4, SEEK_CUR) # skip package flags

        name_table_count = int.from_bytes(self.file.read(4), "little")
        name_table_offset = int.from_bytes(self.file.read(4), "little")
        export_table_count = int.from_bytes(self.file.read(4), "little")
        export_table_offset = int.from_bytes(self.file.read(4), "little")

        if export_table_count > 1:
            raise TypeError("Unreal Package contains more than one exported object.")

        self.file.seek(name_table_offset)
        name_table_index = 0
        names = []
        while name_table_index < name_table_count:
            if version > 61:
                current_name_length = int.from_bytes(self.file.read(1), "little")
                names.append(self.file.read(current_name_length - 1).decode("ascii"))
                self.file.seek(1, SEEK_CUR) # skip terminating zero
            else:
                at_terminating_zero = False
                name = str()
                while not at_terminating_zero:
                    byte = self.file.read(1)
                    if not byte == b"\x00":
                        name += byte.decode()
                    else:
                        names.append(name)
                        at_terminating_zero = True
            self.file.seek(4, SEEK_CUR) # skip  object flags
            name_table_index += 1

        if "Music" not in names:
            raise TypeError("Unreal Package File does not contain music.")

        self.file.seek(export_table_offset)
        self.read_compact_index() # skip class index
        self.read_compact_index() # skip super index
        self.file.seek(4, SEEK_CUR) # skip package index
        self.read_compact_index() # skip object name
        self.file.seek(4, SEEK_CUR) # skip object flags
        self.read_compact_index() # skip serial size
        serial_offset = self.read_compact_index()

        self.file.seek(serial_offset)
        self.file.seek(2, SEEK_CUR) # skip chunk count
        if version > 61:
            self.file.seek(4, SEEK_CUR) # skip following byte position
        chunk_size = self.read_compact_index() # serial size minus the object's header
        embedded_stream = BytesIO(self.file.read(chunk_size))
        embedded_file = identify_module(embedded_stream)

        self.title = embedded_file.title
        self.samples = embedded_file.samples

    def read_compact_index(self):
        """
        Reads a byte (or more depending on continue flags) at self.file's stream
        position.
        Converts these byte(s) from a compact index into an integer, and returns
        it.
        """
        compact_index = ""

        first_byte = int.from_bytes(self.file.read(1), "little")
        if first_byte == 0:
            return 0
        negative_flag = bool(first_byte & 0b10000000)
        continue_flag = bool(first_byte & 0b01000000)
        first_byte_binary = bin(first_byte & 0b00111111)[2:]
        while len(first_byte_binary) < 6:
            first_byte_binary = str(0) + first_byte_binary
        compact_index = first_byte_binary

        while continue_flag:
            other_byte = int.from_bytes(self.file.read(1), "little")
            other_byte_binary = bin(other_byte & 0b01111111)[2:]
            while len(other_byte_binary) < 7:
                other_byte_binary = str(0) + other_byte_binary
            compact_index = other_byte_binary + compact_index
            continue_flag = bool(other_byte & 0b10000000)

        value = int(compact_index, 2)
        if negative_flag:
            value = -value
        return value
