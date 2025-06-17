import os
import uuid
import logging
from datetime import datetime
import functions_framework
from flask import jsonify, make_response

# ——— Logger setup ———
logger = logging.getLogger('travel_booking_function')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
)
if not logger.handlers:
    logger.addHandler(handler)

@functions_framework.http
def travel_booking(request):
    """
    HTTP Cloud Run Function for processing travel bookings.
    Expects a JSON payload:
    {
      "customer_name": "Alice",
      "travel_date": "2025-05-15",
      "origin": "BOM",
      "destination": "DEL",
      "passengers": 2,
      "trip_type": "round_trip"
    }
    Reads two env vars:
      Env      – e.g. "dev", "staging", "prod"
      RunDate  – e.g. "2025-04-26T21:15:00Z"
    """

    # Log env info
    env = os.getenv('Env', 'undefined')
    run_date = os.getenv('RunDate', 'undefined')
    logger.info("Function invoked in Env=%s at RunDate=%s", env, run_date)

    if request.method != 'POST':
        logger.warning("Invalid HTTP method: %s", request.method)
        return make_response(
            jsonify({"error": "Method not allowed; use POST"}), 405
        )

    data = request.get_json(silent=True)
    if not data:
        logger.error("No JSON payload received")
        return make_response(jsonify({"error": "Invalid or missing JSON"}), 400)

    # Required fields
    required = ["customer_name", "travel_date", "origin", "destination", "passengers"]
    missing = [f for f in required if f not in data]
    if missing:
        logger.error("Missing fields: %s", missing)
        return make_response(
            jsonify({"error": f"Missing fields: {missing}"}), 400
        )

    customer = data["customer_name"]
    travel_date_str = data["travel_date"]
    origin = data["origin"]
    destination = data["destination"]
    passengers = data["passengers"]
    trip_type = data.get("trip_type", "one_way")

    logger.info(
        "Booking request: customer=%s, date=%s, route=%s→%s, trip_type=%s, pax=%d",
        customer, travel_date_str, origin, destination, trip_type, passengers
    )

    # Validate travel date
    try:
        travel_date = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Invalid date format: %s", travel_date_str)
        return make_response(
            jsonify({"error": "Invalid date format; use YYYY-MM-DD"}), 400
        )

    if travel_date < datetime.now().date():
        logger.warning("Travel date in the past: %s", travel_date)
        return make_response(
            jsonify({"error": "Travel date cannot be in the past"}), 400
        )

    # Generate booking reference
    booking_ref = f"BK-{uuid.uuid4().hex[:8].upper()}"
    logger.info("Generated booking reference: %s", booking_ref)

    # Build response including env vars
    response_body = {
        "status": "success",
        "booking_reference": booking_ref,
        "customer": customer,
        "travel_date": travel_date_str,
        "route": f"{origin} → {destination}",
        "passengers": passengers,
        "trip_type": trip_type,
        "env": env,
        "run_date": run_date,
        "message": "Your booking has been received and is being processed."
    }

    logger.info("Responding with booking confirmation for %s", booking_ref)
    return make_response(jsonify(response_body), 201)