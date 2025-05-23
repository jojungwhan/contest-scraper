def extract_days_left(dday_text):
    """Extract numeric days left from D-Day text."""
    try:
        # Remove any non-numeric characters except minus sign
        days = ''.join(c for c in dday_text if c.isdigit() or c == '-')
        return int(days) if days else 0
    except:
        return 0 