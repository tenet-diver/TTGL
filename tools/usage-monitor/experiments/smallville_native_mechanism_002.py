#!/usr/bin/env python3
"""Fresh registered continuation; preserve original mechanism implementation."""
import argparse
import smallville_native_mechanism as original
original.ROOT=original.GLOBAL/'smallville-native-mechanism-002'
original.PROTOCOL=original.HERE.parent/'studies/smallville-native-mechanism-protocol-002.json'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    getattr(original,parser.parse_args().action)()
