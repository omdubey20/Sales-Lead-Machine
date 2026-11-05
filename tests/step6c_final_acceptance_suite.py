"""
Compatibility shim redirecting step6c_final_acceptance_suite to the hardened step6d_acceptance_suite.
"""
import asyncio
from tests.step6d_acceptance_suite import run_step6d_acceptance

if __name__ == "__main__":
    asyncio.run(run_step6d_acceptance())
