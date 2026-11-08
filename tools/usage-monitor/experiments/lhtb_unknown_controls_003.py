#!/usr/bin/env python3
"""Fresh zero-model controls after host interruption; original002 preserved."""
import argparse
import lhtb_unknown_controls_002 as original
original.ROOT=original.BASE/'unknown-controls-003'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('condition',choices=['empty','reference'])
    original.run(parser.parse_args().condition)
