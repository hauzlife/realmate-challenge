"""Nightly processing of the property catalog."""

import time


def process_property(description: str) -> str:
    """Process the description of a single listing.

    Simulates the per-listing work of the nightly job, such as enriching the
    listing or syncing it with another system. The sleep stands in for that work.

    Args:
        description: The listing description.

    Returns:
        The processed description.
    """
    # this is simply to simulate a processing job
    time.sleep(0.01)
    processed_description = f"Processed: {description}"
    return processed_description
