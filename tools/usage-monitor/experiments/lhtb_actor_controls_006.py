#!/usr/bin/env python3
"""New control record after dependency ACL preparation correction; source same."""
import argparse
import lhtb_actor_controls as original
from lhtb_actor_runtime_v2 import UnknownActor
original.ROOT=original.BASE/'actor-controls-006'
original.UnknownActor=UnknownActor
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('condition',choices=['boundary','empty','reference']);original.run(parser.parse_args().condition)
