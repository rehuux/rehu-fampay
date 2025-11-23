from flask import Flask, jsonify, request
import requests
import json
import sys

app = Flask(__name__)

WESTEROS_URL = "https://westeros.famapp.in/txn/create/payout/add/"

# IMPORTANT:
# Authorization token expires / changes frequently.
# If API stops working, update the "authorization" token below.
HEADERS = {
    'User-Agent': "A015 | Android 15 | Dalvik/2.1.0 | Tetris | 318D0D6589676E17F88CCE03A86C2591C8EBAFBA |  (Build -1) | 3DB5HIEMMG",
    'Accept': "application/json",
    'Content-Type': "application/json",
    'authorization': "Token eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiZXBrIjp7Imt0eSI6Ik9LUCIsImNydiI6Ilg0NDgiLCJ4IjoicGEwWmVNd255eFBKYXB5ZU9udXlkV1J1OEJWbFlMY1l2YkliUC1FOXhkdUo2dzNGbmNOTDFHMlZqVm9ZZWktOGEzRlRaX29tdGFRIn0sImFsZyI6IkVDREgtRVMifQ.._Fz2hxuGqpjf7V1pCeznsA.g4R7FbdRU3R7m1j3bkSyEljVTsqv8lLCEDy4Vsh2-06j1w1lw4f7ME6j6HB_B_8GMV6H63BR2mU-ogNBW1uKIDDiJQFKn4KkmOdbZX_Gr7y6BIty5FwqV6Tx4pk2NVMdl07eNPyLZZExpp9whLOOxrB02fSxMTptvHMYsSAkQaEt1eHaLkERPSj84loywzsFjWSmgYlr9Tt0MaFoB4Va348_ZFs1JI1sDpq9ZEicW2RBnz2vka2tz_zki-5rj7Enhi9HP5xMoo9XOwvmnvZAAQ.tWG08-yG0nr1vF7VKDUUC4zLHbkB3rYegjW47kP5Vk8",

    # ⭐ REQUIRED HEADERS — Fix for AUTH028 error
    'x-platform': "android",
    'x-platform-version': "15",
    'x-client-version': "4.2025.01.01",

    # optional but recommended
    'accept-encoding': "gzip"
}


def fetch_fampay_pii(upi_id):
    """Fetch PII for FamPay UPI ID"""

    payload = {
        "upi_string": f"upi://pay?pa={upi_id}",
        "init_mode": "00",
        "is_uploaded_from_gallery": False
    }

    try:
        response = requests.post(
            WESTEROS_URL,
            data=json.dumps(payload),
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        user_info = data.get("user", {})

        if not user_info:
            return {
                "error": f"'user' object not found in response for {upi_id}.",
                "developer": "@istgrehu",
                "status_code": 404
            }

        first_name = user_info.get("first_name", "")
        last_name = user_info.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        phone_number = user_info.get("contact", {}).get("phone_number")

        return {
            "name": full_name,
            "upi_id": upi_id,
            "mobile_number": phone_number,
            "developer": "@istgrehu"
        }

    except requests.exceptions.HTTPError as e:
        return {
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "status_code": e.response.status_code,
            "developer": "@istgrehu"
        }

    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection Error: {e}", "developer": "@istgrehu", "status_code": 503}

    except requests.exceptions.Timeout:
        return {"error": "API Request Timed Out", "developer": "@istgrehu", "status_code": 408}

    except requests.exceptions.RequestException as e:
        return {"error": f"Unexpected Error: {e}", "developer": "@istgrehu", "status_code": 500}

    except json.JSONDecodeError:
        return {"error": "Invalid JSON from FamPay API", "developer": "@istgrehu", "status_code": 500}

    except Exception as e:
        return {"error": f"Internal Server Error: {e}", "developer": "@istgrehu", "status_code": 500}


@app.route('/fampay_pii', methods=['GET'])
def get_fampay_pii():

    upi_id = request.args.get('upi_id')

    if not upi_id:
        return jsonify({
            "error": "Missing 'upi_id' parameter",
            "developer": "@istgrehu"
        }), 400

    # Warning only
    if "@fam" not in upi_id.lower():
        print(f"[!] Warning: '{upi_id}' is not a @fam UPI", file=sys.stderr)

    result = fetch_fampay_pii(upi_id)

    if "error" in result:
        code = result.get("status_code", 500)
        return jsonify(result), code

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)