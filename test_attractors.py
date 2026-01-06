#!/usr/bin/env python3
"""Test script to validate attractor computation without GUI."""

import sys
import numpy as np
from attractors import lorenz, rossler, thomas, aizawa, rk4_integrate, ATTRACTORS


def test_attractor(name, attractor_def):
    """Test that an attractor can be computed without errors."""
    print(f"\nTesting {name} attractor...")

    deriv = attractor_def["deriv"]
    params = attractor_def["params"]
    initial = np.array([0.1, 0.0, 0.0], dtype=float)
    dt = 0.01
    steps = 1000

    try:
        data = rk4_integrate(deriv, initial, params, dt, steps)

        # Basic validation
        assert data.shape == (steps, 3), f"Expected shape ({steps}, 3), got {data.shape}"
        assert not np.any(np.isnan(data)), "Data contains NaN values"
        assert not np.any(np.isinf(data)), "Data contains Inf values"

        print(f"  ✓ Integration successful")
        print(f"  ✓ Generated {steps} points")
        print(f"  ✓ Data range: X[{data[:,0].min():.2f}, {data[:,0].max():.2f}], "
              f"Y[{data[:,1].min():.2f}, {data[:,1].max():.2f}], "
              f"Z[{data[:,2].min():.2f}, {data[:,2].max():.2f}]")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run tests on all attractors."""
    print("=" * 60)
    print("Attractor Explorer - Validation Test")
    print("=" * 60)

    all_passed = True

    for name, attractor_def in ATTRACTORS.items():
        passed = test_attractor(name, attractor_def)
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
