#!/usr/bin/env python3
"""Use the same policy runner with a separately identified compact expert backend."""
import run_policy_study as driver
from ttgl.compact import CompactPolicyBackend

if __name__ == '__main__':
    driver.policy.PolicyBackend=CompactPolicyBackend
    driver.main()
