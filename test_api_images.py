
import requests

API_URL = "http://127.0.0.1:8001"

passed = []
failed = []

for image_id in range(1, 21):
    try:
        response = requests.get(
            f"{API_URL}/images/{image_id}/view",
            timeout=60,
        )

        if response.status_code == 200 and len(response.content) > 0:
            passed.append(image_id)
            print(
                f"PASS: Image {image_id} "
                f"({len(response.content):,} bytes)"
            )
        else:
            failed.append(image_id)
            print(
                f"FAIL: Image {image_id} "
                f"(HTTP {response.status_code})"
            )

    except requests.RequestException as error:
        failed.append(image_id)
        print(f"FAIL: Image {image_id} ({error})")

print("\n--- TEST SUMMARY ---")
print(f"Passed: {len(passed)}/20")
print(f"Failed: {len(failed)}/20")

if failed:
    print("Failed image IDs:", failed)
