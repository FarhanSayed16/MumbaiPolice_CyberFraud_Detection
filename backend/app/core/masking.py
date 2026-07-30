from typing import Optional


def mask_account_number(account_number: Optional[str]) -> Optional[str]:
    """
    Masks bank account numbers for list APIs and general officer UI (`Sub-phase 5.2`).
    Example: '981273491283' -> '•••• •••• 1283'
    """
    if not account_number:
        return None
    cleaned = account_number.strip()
    if len(cleaned) <= 4:
        return "•••• " + cleaned
    last_four = cleaned[-4:]
    return f"•••• {last_four}"


def mask_ifsc(ifsc_code: Optional[str]) -> Optional[str]:
    """
    Masks middle characters of IFSC codes while retaining bank prefix and branch suffix.
    Example: 'SBIN0001234' -> 'SBIN••••234'
    """
    if not ifsc_code:
        return None
    cleaned = ifsc_code.strip()
    if len(cleaned) <= 7:
        return "••••"
    return f"{cleaned[:4]}••••{cleaned[-3:]}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """
    Masks phone/mobile numbers showing only last 4 digits.
    Example: '+919876543210' -> '••••••3210'
    """
    if not phone:
        return None
    cleaned = phone.strip()
    if len(cleaned) <= 4:
        return "•••• " + cleaned
    return f"••••••{cleaned[-4:]}"


def mask_email(email: Optional[str]) -> Optional[str]:
    """
    Masks local part of email for list APIs (audit M11/E6).
    Example: 'rajesh.kumar@example.com' -> 'r••••r@example.com'
    """
    if not email or "@" not in email:
        return email
    local, _, domain = email.strip().partition("@")
    if len(local) <= 2:
        masked_local = "••"
    else:
        masked_local = f"{local[0]}••••{local[-1]}"
    return f"{masked_local}@{domain}"


def mask_upi_id(upi_id: Optional[str]) -> Optional[str]:
    """
    Masks local part of UPI ID before @ handle.
    Example: 'fraudster@okicici' -> 'f••••r@okicici'
    """
    if not upi_id or "@" not in upi_id:
        return mask_account_number(upi_id)
    parts = upi_id.split("@")
    local = parts[0]
    handle = parts[1] if len(parts) > 1 else ""
    if len(local) <= 2:
        masked_local = "••"
    else:
        masked_local = f"{local[0]}••••{local[-1]}"
    return f"{masked_local}@{handle}"
