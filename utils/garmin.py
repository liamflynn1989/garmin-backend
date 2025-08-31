import os
import datetime
import pickle
import pandas as pd
from garminconnect import Garmin, GarminConnectTooManyRequestsError, GarminConnectConnectionError
from dotenv import load_dotenv
import time

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()


USERS = {
    "Liam": {"email": os.environ["LIAM_EMAIL"], "password": os.environ["LIAM_PASSWORD"]},
    "Nawaaaz": {"email": os.environ["WAAAZ_EMAIL"], "password": os.environ["WAAAZ_PASSWORD"]},
    "Cormo": {"email": os.environ["CORMO_EMAIL"], "password": os.environ["CORMO_PASSWORD"]},
}

SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

def get_session_path(username: str):
    safe_username = username.replace("@", "_at_").replace(".", "_dot_")
    return os.path.join(SESSION_DIR, f"{safe_username}.pickle")

def login_garmin(email, password, session_path):
    try:
        client = Garmin(email, password)
        client.login()
        with open(session_path, "wb") as f:
            pickle.dump(client, f)
        logging.info(f"✅ Logged in and saved session: {session_path}")
        return client
    except GarminConnectTooManyRequestsError:
        logging.info("❌ Too many requests — backing off.")
        raise
    except Exception as e:
        logging.info(f"❌ Failed login for {email}: {e}")
        raise

def load_or_login(user: str, email: str, password: str):
    session_path = get_session_path(email)
    client = None

    if os.path.exists(session_path):
        try:
            with open(session_path, "rb") as f:
                client = pickle.load(f)
            # test session is valid
            client.get_body_battery(datetime.date.today())
            logging.info(f"✅ Loaded session for {email}")
            return client
        except Exception as e:
            logging.info(f"⚠️ Failed to reuse session for {email}, retrying login: {e}")

    # fallback to fresh login
    return login_garmin(email, password, session_path)

def fetch_body_battery(email, password):
    session_path = get_session_path(email)
    client = load_or_login(email, email, password)
    data = client.get_body_battery(datetime.date.today())
    return data

def fetch_all_users():
    result = {}
    for name, creds in USERS.items():
        try:
            logging.info(f"🔄 Fetching for {name}...")
            data = fetch_body_battery(creds["email"], creds["password"])

            if not data or "bodyBatteryValuesArray" not in data[0]:
                logging.info(f"⚠️ No valid data for {name}")
                result[name] = []
                continue

            df = pd.DataFrame(data[0]["bodyBatteryValuesArray"], columns=["timestamp_ms", "body_battery"])
            if not df.empty:
                df['body_battery'] = df['body_battery'].fillna(method="ffill").fillna(method="bfill")

            result[name] = df.to_dict(orient="records")
            time.sleep(3)  # avoid triggering rate limits
        except GarminConnectTooManyRequestsError:
            logging.info(f"🚫 Rate limited while fetching {name} — skipping.")
        except Exception as e:
            logging.info(f"❌ Error fetching data for {name}: {e}")
    return result