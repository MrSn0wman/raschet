"""Daily retention cleanup: run with the same environment/service account as API."""
from dotenv import load_dotenv
load_dotenv()
import db

def main():
    db.init_db()
    conn = db.connect()
    try:
        deleted = db.purge_expired_feedback(conn)
        conn.commit()
    finally:
        conn.close()
    # init_db also purges: do not report only the second DELETE as the total.
    print("Feedback retention cleanup completed.")

if __name__ == "__main__":
    main()
