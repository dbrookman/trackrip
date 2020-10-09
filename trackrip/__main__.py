"""Rips all samples contained in a specified tracker music file to WAV."""

import argparse
from pathlib import Path
import string
import wave
from . import tracker

def main():
    """Parses, opens and extracts samples from a tracker module file."""

    parser = argparse.ArgumentParser()
    parser.add_argument("mod", help="a valid MOD, S3M or IT file", type=Path)
    parser.add_argument("-o", "--output_path", type=Path)

    args = parser.parse_args()

    with open(args.mod, "rb") as file:
        if args.output_path:
            output_path = Path(Path.cwd(), args.output_path).resolve()
            if not Path(output_path).is_dir():
                raise NotADirectoryError("Output directory does not exist.")
        else:
            output_path = Path(Path.cwd())

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

                output = output_path / sample_file_name
                out = wave.open(str(output), "wb")
                out.setnchannels(1)
                out.setsampwidth(sample["width"])
                out.setframerate(sample["rate"])
                out.writeframes(sample["data"])
                out.close()


if __name__ == "__main__":
    main()
