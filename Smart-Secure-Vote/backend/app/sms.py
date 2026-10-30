def send_otp(phone: str, code: str) -> None:
    # Demo-only provider: never sends a real SMS.
    print(f"[MOCK SMS] OTP for {phone}: {code}")
