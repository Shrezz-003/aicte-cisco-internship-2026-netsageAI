import re
from typing import List, Dict


def run_deterministic_checks(show_outputs: str) -> List[Dict[str, str]]:
    """
    Scans raw Cisco CLI output for obvious, deterministic network errors.
    Acts as a pre-filter before sending complex logic to the AI.
    """
    if not show_outputs:
        return []

    detected_errors = []

    # 1. Interface States (Administratively down or physically down)
    if re.search(r'is (administratively )?down,\s*line protocol is down', show_outputs):
        detected_errors.append({
            "rule": "Interface Status",
            "message": "One or more interfaces are shut down or physically disconnected."
        })

    # 2. IP Address Conflicts
    if re.search(r'Duplicate address', show_outputs, re.IGNORECASE):
        detected_errors.append({
            "rule": "IP Conflict",
            "message": "A duplicate IP address conflict was detected in the logs."
        })

    # 3. OSPF MTU Mismatch (Stuck in EXSTART)
    if re.search(r'EXSTART', show_outputs):
        detected_errors.append({
            "rule": "OSPF State Error",
            "message": "OSPF neighbor stuck in EXSTART state. Highly indicative of an MTU mismatch."
        })

    # 4. DHCP Pool Exhaustion
    # Matches patterns like: Total addresses: 254, Leased addresses: 254
    if re.search(r'Total addresses\s*:\s*(\d+)\s*Leased addresses\s*:\s*\1', show_outputs):
        detected_errors.append({
            "rule": "DHCP Exhaustion",
            "message": "100% of DHCP pool addresses are currently leased."
        })

    # 5. Missing NAT Configuration
    if "show ip nat translations" in show_outputs and "show run" in show_outputs:
        if not re.search(r'ip nat (inside|outside)', show_outputs):
            detected_errors.append({
                "rule": "NAT Configuration",
                "message": "Missing 'ip nat inside' or 'ip nat outside' on interfaces."
            })

    return detected_errors


# Quick local test if you run this script directly
if __name__ == "__main__":
    sample_output = """
    GigabitEthernet0/0 is administratively down, line protocol is down
    Neighbor ID 10.0.0.1 Pri 0 State EXSTART/ - 00:00:32
    """
    print(run_deterministic_checks(sample_output))