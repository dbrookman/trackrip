# trackrip
_(tracker-rip)_

Extracts samples from various music tracker module formats.

- Currently supports the following formats:
    - __MOD__
    - __S3M__
    - __IT__
    - __XM__
    - __UMX__
- Embeds sample loop parameters from the module into exported WAV files.

## Installation

`pip3 install trackrip`

Alternatively, you can download the source and run:

`python3 setup.py install`

## Usage

`trackrip <module_file>`

## Useful Links
### ProTracker MOD Format
* [Noisetracker/Soundtracker/Protracker Module Format](https://www.aes.id.au/modformat.html) -  4th Revision
* [Protracker Module](https://wiki.multimedia.cx/index.php/Protracker_Module) on MultimediaWiki
* [MOD Player Tutorial](https://modland.com/pub/documents/format_documentation/FireLight%20MOD%20Player%20Tutorial.txt) by FireLight
### Scream Tracker 3 S3M Format
* [Scream Tracker 3.01 BETA File Formats And Mixing Info](http://www.textfiles.com/programming/FORMATS/s3m-form.txt)
* [S3M Format](http://www.shikadi.net/moddingwiki/S3M_Format) on the DOS Game Modding Wiki
* [S3M Player Tutorial](https://modland.com/pub/documents/format_documentation/FireLight%20S3M%20Player%20Tutorial.txt) by FireLight
### Impulse Tracker IT Format
* [ITTECH.TXT](https://ia600506.us.archive.org/view_archive.php?archive=/4/items/msdos_it214c_shareware/it214c.zip&file=ITTECH.TXT)
* [IT214 sample compression](https://wiki.multimedia.cx/index.php/Impulse_Tracker#IT214_sample_compression) on MultimediaWiki
### FastTracker 2 XM (Extended Module) Format
* [The XM Module Format Description for XM Files Version $0104](https://ftp.modland.com/pub/documents/format_documentation/FastTracker%202%20v2.04%20(.xm).html) by Mr.H, with corrections from Guru & Alfred of Sahara Surfers
* [The "Complete" XM module format specification](https://github.com/milkytracker/MilkyTracker/blob/master/resources/reference/xm-form.txt) by ccr - v0.81
* [The Unofficial XM File Format Specification](https://www.celersms.com/doc/XM_file_format.pdf) by Vladimir Kameñar
### Unreal Engine UMX Container Format
* [Unreal Packages](https://web.archive.org/web/19991006025316fw_/http://unreal.epicgames.com/Packages.htm) by Tim Sweeney
* [Unreal Tournament Package File Format](https://bunnytrack.net/ut-package-format/) by Sapphire
* [Package File Format](https://wiki.beyondunreal.com/Legacy:Package_File_Format) on Unreal Wiki
* [UT Package File Format document v1.6](https://www.acordero.org/download/utpdldoc16/) by Antonio Cordero Balcázar
