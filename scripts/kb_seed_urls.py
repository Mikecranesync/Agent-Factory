#!/usr/bin/env python3
"""
KB Seed URLs - Curated list of industrial PLC/automation PDF manuals

These URLs are pushed to the VPS KB Factory Redis queue for ingestion.
Target: 100+ knowledge atoms from high-quality sources.
"""

# =============================================================================
# ALLEN-BRADLEY / ROCKWELL AUTOMATION
# =============================================================================
ALLEN_BRADLEY_URLS = [
    # ControlLogix
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",  # ControlLogix System User Manual
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/pm/1756-pm001_-en-p.pdf",  # Logix5000 Controllers General Instructions
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/rm/1756-rm003_-en-p.pdf",  # Logix5000 Controllers Motion Instructions

    # CompactLogix
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1769-um021_-en-p.pdf",  # CompactLogix 5380 Controllers User Manual

    # Studio 5000
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um022_-en-p.pdf",  # Studio 5000 Logix Designer User Manual

    # PowerFlex Drives
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/750-um001_-en-p.pdf",   # PowerFlex 750-Series User Manual
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/520-um001_-en-p.pdf",   # PowerFlex 520-Series User Manual

    # PanelView HMI
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/2711p-um001_-en-p.pdf", # PanelView Plus 7 User Manual

    # Safety
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um020_-en-p.pdf",  # GuardLogix Safety Controllers
]

# =============================================================================
# SIEMENS
# =============================================================================
SIEMENS_URLS = [
    # S7-1200
    "https://support.industry.siemens.com/cs/attachments/109814829/s71200_system_manual_en-US_en-US.pdf",

    # S7-1500
    "https://support.industry.siemens.com/cs/attachments/109747136/s71500_system_manual_en-US_en-US.pdf",

    # TIA Portal (if accessible)
    # Note: Siemens often requires login for full manuals
]

# =============================================================================
# MITSUBISHI
# =============================================================================
MITSUBISHI_URLS = [
    # MELSEC iQ-R Series
    "https://dl.mitsubishielectric.com/dl/fa/document/manual/plc/sh080483eng/sh080483engap.pdf",  # iQ-R CPU User Manual

    # GX Works3
    "https://dl.mitsubishielectric.com/dl/fa/document/manual/plc/sh081215eng/sh081215engae.pdf",  # GX Works3 Operating Manual
]

# =============================================================================
# OMRON
# =============================================================================
OMRON_URLS = [
    # NX/NJ Series
    "https://assets.omron.eu/downloads/manual/en/w501_nx-series_cpu_unit_users_manual_en.pdf",

    # Sysmac Studio
    "https://assets.omron.eu/downloads/manual/en/w504_sysmac_studio_operation_manual_en.pdf",
]

# =============================================================================
# SCHNEIDER ELECTRIC / MODICON
# =============================================================================
SCHNEIDER_URLS = [
    # Modicon M340
    "https://download.schneider-electric.com/files?p_Doc_Ref=EIO0000001578&p_enDocType=User%20guide&p_File_Name=EIO0000001578.00.pdf",

    # Unity Pro
    "https://download.schneider-electric.com/files?p_Doc_Ref=EIO0000000071&p_enDocType=User%20guide&p_File_Name=EIO0000000071.03.pdf",
]

# =============================================================================
# ABB
# =============================================================================
ABB_URLS = [
    # AC500 PLC
    # Note: ABB requires account for most manuals - add accessible ones here
]

# =============================================================================
# COMBINED LIST
# =============================================================================
SEED_URLS = (
    ALLEN_BRADLEY_URLS +
    SIEMENS_URLS +
    MITSUBISHI_URLS +
    OMRON_URLS +
    SCHNEIDER_URLS +
    ABB_URLS
)

# Metadata for tracking
URL_METADATA = {
    "allen_bradley": len(ALLEN_BRADLEY_URLS),
    "siemens": len(SIEMENS_URLS),
    "mitsubishi": len(MITSUBISHI_URLS),
    "omron": len(OMRON_URLS),
    "schneider": len(SCHNEIDER_URLS),
    "abb": len(ABB_URLS),
    "total": len(SEED_URLS),
}

if __name__ == "__main__":
    print("=" * 60)
    print("KB Seed URLs Summary")
    print("=" * 60)
    for manufacturer, count in URL_METADATA.items():
        if manufacturer != "total":
            print(f"  {manufacturer.replace('_', ' ').title()}: {count} PDFs")
    print("-" * 60)
    print(f"  TOTAL: {URL_METADATA['total']} PDFs")
    print("=" * 60)
    print("\nURLs to ingest:")
    for i, url in enumerate(SEED_URLS, 1):
        print(f"  {i}. {url[:80]}...")
