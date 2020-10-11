"""Rips all samples contained in a specified tracker music file to WAV."""

import argparse
from pathlib import Path
import string
import wave
from math import floor
from . import tracker

def main():
    """Parses, opens and extracts samples from a tracker module file."""

    parser = argparse.ArgumentParser()
    parser.add_argument("mod", help="a valid MOD, S3M or IT file", type=Path)
    parser.add_argument("-o", "--output_dir", type=Path)

    args = parser.parse_args()

    with open(args.mod, "rb") as file:
        if args.output_dir:
            output_dir = Path(Path.cwd(), args.output_dir).resolve()
            if not Path(output_dir).is_dir():
                raise NotADirectoryError("Output directory does not exist.")
        else:
            output_dir = Path(Path.cwd())

        mod_file = tracker.identify_module(file)
        print("TITLE: " + mod_file.title)

        for sample in mod_file.samples:
            sample_file_name = ""
            if sample["length"] > 0:
                sample_file_name = str(sample["number"])
                sample["name"] = "".join(filter(lambda x: x in set(string.printable), sample["name"]))
                if sample["name"] != "":
                    sample_file_name += " - " + sample["name"]
                keepcharacters = (" ", ".", "_", "-")
                sample_file_name = "".join(c for c in sample_file_name if
                                           c.isalnum() or c in
                                           keepcharacters).rstrip()
                print("[Exporting Sample] " + sample_file_name)
                sample_file_name += ".wav"

                output_path = output_dir / sample_file_name
                out = wave.open(str(output_path), "wb")
                out.setnchannels(1)
                out.setsampwidth(sample["width"])
                out.setframerate(sample["rate"])
                out.writeframes(sample["data"])
                out.close()

                if sample["loop_start"] and sample["loop_end"]:
                    smpl_chunk = b"smpl"
                    # chunk size
                    smpl_chunk += int(36 + (1 * 24) + 0).to_bytes(4, "little")
                    # manufacturer & product
                    smpl_chunk += bytes(8)
                    # saample period
                    smpl_chunk += int(floor(1000000000 / sample["rate"])).to_bytes(4, "little")

                    # TODO: figure me out
                    # midi unity note
                    smpl_chunk += bytes(4)
                    # midi pitch fraction
                    smpl_chunk += bytes(4)

                    # smpte format & offset
                    smpl_chunk += bytes(8)
                    # number of sampler loops (should always be 1)
                    smpl_chunk += int(1).to_bytes(4, "little")
                    # sampler data
                    smpl_chunk += bytes(4)
                    # sample loops
                    # cue point ID, type
                    smpl_chunk += bytes(8)
                    # loop start
                    smpl_chunk += int(sample["loop_start"]).to_bytes(4, "little")
                    # loop end
                    smpl_chunk += int(sample["loop_end"] - 1).to_bytes(4, "little")
                    # fration, play count
                    smpl_chunk += bytes(8)

                    with open(output_path, "ab") as file:
                        file.write(smpl_chunk)


if __name__ == "__main__":
    main()
