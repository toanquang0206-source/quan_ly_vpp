import bcrypt
def hash_password(plain: str) -> str:
    """Băm mật khẩu"""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
def verify_password(plain: str, hashed: str) -> bool:
    "Kiểm tra"
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))