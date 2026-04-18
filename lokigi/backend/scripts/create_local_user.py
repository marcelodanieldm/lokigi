import sys

from app.database import SessionLocal
from app.models import User


def main() -> int:
    email = sys.argv[1] if len(sys.argv) > 1 else "local@example.com"
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            print(str(existing.id))
            return 0

        user = User(email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
        print(str(user.id))
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
