import sqlite3
import logging
import time
import sys

from datetime import datetime


class DailyLimitExceededError(Exception):
    """Raised when the daily quota of 250 requests is reached."""
    pass


logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO 
)


class RateLimiter:
    def __init__(self, db_path='request_logs.db'):
        self.db_path = db_path
        self._init_db()

        # Configuration Constants
        self.MAX_RPM = 4            # Rule #1 - Requests per minute
        self.MAX_TPM = 250_000        # Rule #2 - Tokens per minute
        self.MAX_RPD = 20            # Rule #3 - Requests per day

        self.logger = logging.getLogger(__name__)

    def _init_db(self):
        """Setup the table and index if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    timestamp REAL,
                    tokens INTEGER
                )
            ''')
            # Index is crucial for performance since we filter by timestamp constantly
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_ts ON requests(timestamp)')

    def wait_for_slot_gemini_free_tier(self, tokens: int):
        """
        Checks if a request can be made.
        - Raises DailyLimitExceededError if daily limit hit.
        - Sleeps 60s and retries if minute limits hit.
        - Returns True when clear.
        """
        while True:
            now = time.time()
            one_minute_ago = now - 60
            one_day_ago = now - 86400

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 1. Check Daily Limit (Rule #3)
                cursor.execute(
                    'SELECT COUNT(*) FROM requests WHERE timestamp > ?',
                    (one_day_ago,)
                )
                daily_requests = cursor.fetchone()[0]

                if daily_requests >= self.MAX_RPD:
                    cursor.execute(
                        'SELECT * FROM requests ORDER BY timestamp'
                    )
                    first_request_timestamp = cursor.fetchone()[0]
                    first_request_dt = datetime.fromtimestamp(
                        first_request_timestamp)

                    raise DailyLimitExceededError(
                        f"Daily limit reached: {daily_requests}/{self.MAX_RPD} requests in the last 24h. First request made at {first_request_dt}"
                    )
                else:
                    self.logger.info(
                        f'Rule #3 OK - daily requests:\t {daily_requests}\t\t (max: {self.MAX_RPD})')

                # 2. Check Minute Limits (Rule #1 & #2)
                cursor.execute(
                    'SELECT COUNT(*), SUM(tokens) FROM requests WHERE timestamp > ?',
                    (one_minute_ago,)
                )
                row = cursor.fetchone()
                minute_requests = row[0]
                # If SUM is None (no rows), treat it as 0
                minute_tokens = row[1] if row[1] is not None else 0

                # 3. Decision Logic
                rpm_ok = minute_requests < self.MAX_RPM
                tpm_ok = minute_tokens < (self.MAX_TPM + tokens)

                if rpm_ok and tpm_ok:
                    self.logger.info(
                        f'Rule #1 OK - minute requests:\t {minute_requests}\t\t (max: {self.MAX_RPM})')
                    self.logger.info(
                        f'Rule #2 OK - minute tokens:\t {minute_tokens} (+{tokens})\t (max: {self.MAX_TPM})')
                    
                    self.log_request(tokens)
                    return True

                # If we are here, we hit a minute limit.
                self.logger.info(
                    f"Limit hit (Reqs: {minute_requests}/{self.MAX_RPM}, Tokens: {minute_tokens}/{self.MAX_TPM}). Waiting 60s...")
                time.sleep(60)
                # The loop will now restart and check again

    def log_request(self, tokens: int):
        """
        Logs a completed request and cleans up old data.
        """
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            # Insert the new record
            conn.execute(
                'INSERT INTO requests (timestamp, tokens) VALUES (?, ?)',
                (now, tokens)
            )

            # Optimization: Delete records older than 24 hours + small buffer.
            # We don't need them for any calculation anymore.
            cleanup_threshold = now - 86500
            conn.execute('DELETE FROM requests WHERE timestamp < ?',
                         (cleanup_threshold,))
            conn.commit()
