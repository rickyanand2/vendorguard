# trust/utils.py
import os
from uuid import uuid4


def cert_artifact_path(instance, filename):
    """
    Builds file path for certification uploads tied to vendor.
    """
    ext = filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"
    vendor_id = getattr(instance, "vendor_id", "unknown")
    return os.path.join("certifications", str(vendor_id), filename)
