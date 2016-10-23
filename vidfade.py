#!/usr/bin/env python3


import argparse
import re
import subprocess
import sys


def to_seconds(duration):
    '''
    Given string input hh:mm:ss.ss, return in seconds
    '''
    p = re.compile("(\d+):(\d+):(\d+)\.(\d+)")
    match = p.match(duration)

    if match:
        h, m, s, hs = map(int, match.groups())
        return 3600*h + 60*m + s + float("0." + str(hs))
    else:
        raise Exception("Unable to find duration of video")


def get_duration(filename):
    proc = subprocess.Popen(["ffmpeg", "-i", filename], stderr=subprocess.PIPE)
    _, stderr = proc.communicate()

    p = re.compile("\n\s*DURATION\s*:\s*(\S+)\s*\n")
    m = p.search(stderr.decode("utf-8"))
    return to_seconds(m.groups()[0])


def get_fade_str(start, duration, fade, in_out):
    '''
    Example: "fade=in:st=0:d=2", fade video from seconds 0:2
    '''
    return "%s=%s:st=%s:d=%s" % (fade, in_out, start, duration)


def get_fade_args(args):
    '''
    Return FFMPEG arguments as a list (for subprocess)
    '''
    vfade_strs = []
    afade_strs = []

    maybe_float = lambda f: float(f) if f else None
    vfi, vfo, afi, afo = map(maybe_float, [
        args.video_fade_in, args.video_fade_out,
        args.audio_fade_in, args.audio_fade_out])

    duration = get_duration(args.INPUT_FILE)

    if vfi:
        vfade_strs.append(get_fade_str(0, vfi, "fade", "in"))
    if vfo:
        vfade_strs.append(get_fade_str(duration - vfo, vfo, "fade", "out"))
    if afi:
        afade_strs.append(get_fade_str(0, afi, "afade", "in"))
    if afo:
        afade_strs.append(get_fade_str(duration - afo, afo, "afade", "out"))

    # Join fade-in and fade-out commands by comma
    vfade_args = ["-filter:v"] + [",".join(vfade_strs)] if vfade_strs else []
    afade_args = ["-af"] + [",".join(afade_strs)] if afade_strs else []

    return vfade_args + afade_args


def main():
    # Descriptions
    DESC = "A simple frontend to FFMPEG for adding fade-in/fade-out effects"
    FADE_HELP = ("Fade %s both the audio and video of the %s DURATION"
            "number of seconds. If DURATION is not specified, defaults to: 2")
    ADV_FADE_HELP = ("Fade %s the %s of the %s DURATION number of seconds. "
            "Will override any values set with -in/--fade-in and -out/--fade-out")

    # Parse Args
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("-in", "--fade-in", metavar="DURATION",
            nargs="?", const=2, type=float,
            help=FADE_HELP%("in", "first"))
    parser.add_argument("-out", "--fade-out", metavar="DURATION",
            nargs="?", const=2, type=float,
            help=FADE_HELP%("out", "last"))

    parser.add_argument("-afi", "--audio-fade-in", metavar="DURATION",
            help=ADV_FADE_HELP%("in", "audio", "first")
            )
    parser.add_argument("-afo", "--audio-fade-out", metavar="DURATION",
            help=ADV_FADE_HELP%("out", "audio", "last")
            )
    parser.add_argument("-vfi", "--video-fade-in", metavar="DURATION",
            help=ADV_FADE_HELP%("in", "video", "first")
            )
    parser.add_argument("-vfo", "--video-fade-out", metavar="DURATION",
            help=ADV_FADE_HELP%("out", "video", "last")
            )


    parser.add_argument("INPUT_FILE", help="Input video file")
    parser.add_argument("OUTPUT_FILE", help="Output video file")

    args = parser.parse_args()

    if args.fade_in:
        if not args.video_fade_in:
            args.video_fade_in = args.fade_in
        if not args.audio_fade_in:
            args.audio_fade_in = args.fade_in

    if args.fade_out:
        if not args.video_fade_out:
            args.video_fade_out = args.fade_out
        if not args.audio_fade_out:
            args.audio_fade_out = args.fade_out


    # Get FFMPEG args
    fade_args = get_fade_args(args)
    cmd = ["ffmpeg", "-i", args.INPUT_FILE] + fade_args + [args.OUTPUT_FILE]

    print(" ".join(cmd))

    # Run
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
