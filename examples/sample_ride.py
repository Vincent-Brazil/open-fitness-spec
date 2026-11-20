"""Preview a sample ride, or test delivery with a registered passport client."""
import argparse
import json
import sys
from pathlib import Path

from passport_quickstart import PASSPORT, PORT, call, connect


def run(sample, client_id=None, base=PASSPORT, port=PORT):
    activity = json.loads((Path(__file__).parent / "rides" / (sample + ".json")).read_text(encoding="utf-8"))
    print(json.dumps(activity, indent=2))
    if not client_id:
        return
    grant = connect(base, client_id, "write detail_write", port)
    if not {"write", "detail_write"} <= set(grant["scope"].split()):
        print("Sending this example needs both ride permissions. No ride was sent.")
        return
    def send():
        return call(base, "/v1/activities", token=grant["access_token"], payload=activity)

    first = send()
    print("First receipt:", first)
    second = send()
    print("Retry receipt:", second)
    if first["ride_id"] != second["ride_id"] or second["created"] is not False:
        raise RuntimeError("Expected the retry to return the original ride ID with created=false.")
    print("Both deliveries refer to passport ride", first["ride_id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample", choices=("route", "workout", "game"))
    parser.add_argument("--client-id", help="Send this sample to a test passport using your passport client ID")
    args = parser.parse_args()
    try:
        run(args.sample, args.client_id)
    except (OSError, RuntimeError) as error:
        sys.exit(str(error))
