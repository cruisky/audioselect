#!/usr/bin/env python
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import sys, os, argparse

def fmt_hms(millis):
    s, ms = divmod(millis, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d.%03d" % (h, m, s, ms)

def is_in_range(v, lo, hi=float('inf')):
    return lo <= v <= hi

def eval_file(fname, selector, callback):
    name, extention = os.path.splitext(fname)
    if extention in (".mp3", ".wma", ".wav", ".m4a", ".ogg"):
        extention = extention[1:] # remove leading dot
        try:
            seg = AudioSegment.from_file(fname, extention)
            callback(fname, selector.selects(seg), seg)
        except CouldntDecodeError:
            pass

def eval_dir(dname, selector, callback):
    for root, dirs, files in os.walk(dname):
        for fname in files:
            eval_file(os.path.join(root, fname), selector, callback)

def eval_tree(name, selector, callback):
    if os.path.isdir(name):
        eval_dir(name, selector, callback)
    elif os.path.isfile(name):
        eval_file(name, selector, callback)

class AudioSelector(list):
    def selects(self, seg):
        return all(map(lambda f: f(seg), self))

    def add_filter_rms(self, lo=0, hi=float('inf')):
        self.append(lambda seg: is_in_range(seg.rms, lo, hi))

    def add_filter_dbfs(self, lo=-float('inf'), hi=0):
        self.append(lambda seg: is_in_range(seg.dBFS, lo, hi))

def cb_print(name, value, seg):
    if value:
        print(name)
def cb_print_info(name, value, seg):
    if value:
        print("'%s' %d %f"%(name, seg.rms, seg.dBFS))

def main():
    parser = argparse.ArgumentParser(
        prog='audioselect',
        description='''
            An audio file selector that analyzes files and prints 
            those that meet the requirement. Only supports loudness. '''
    )
    parser.add_argument('files', nargs='*', 
        help='One or more audio files or directories containing audio files'
    )
    parser.add_argument('--show-value', 
        action='store_true',
        help='Display all measured values after each selected entry.'
    )
    parser.add_argument('--exclude',
        action='store_true',
        help='Print audio files that don\'t meet the requirement.'
        )
    parser.add_argument('--rms', nargs=2, type=int, 
        help='Range of RMS value.' 
    )
    parser.add_argument('--dbfs', nargs=2, type=float, 
        help='Range of dBFS value.'
    )

    args = parser.parse_args()

    # construct selector
    selector = AudioSelector()
    if args.rms:
        selector.add_filter_rms(args.rms[0], args.rms[1])
    if args.dbfs:
        selector.add_filter_dbfs(args.dbfs[0], args.dbfs[1])

    # construct callback function
    callback_base = cb_print                # default callback
    if args.show_value:
        callback_base = cb_print_info

    if args.exclude:
        callback = lambda name, result, seg: callback_base(name, not result, seg)
    else:
        callback = callback_base

    # evaluate the files or inputs
    for path in args.files if args.files else sys.stdin:
        eval_tree(path.strip(), selector, callback)

def test():
    song = AudioSegment.from_file("../The Butterfly Effect.mp3")
    print("frame rate:", song.frame_rate)
    print("frame width:", song.frame_width)
    print("sample width:", song.sample_width)
    print("channels:", song.channels)
    print("dBFS:", song.dBFS)
    print("rms:", song.rms)

if __name__ == '__main__':
    main()
