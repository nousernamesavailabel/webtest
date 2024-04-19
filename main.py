import requests
import schedule
import time
from datetime import datetime, timedelta
from simplepush import send

url = "http://webpt.com"

# Define your SimplePush API key
API_KEY = "APIKEY"

#send(API_KEY, f"Monitoring {url}")

# Dictionary to store last notification time for each response status
last_notification_time = {}
# Dictionary to store response code counts
response_counts = {"total": 0, "non_200": 0}


def send_get_request():
    url = "http://webpt.com"
    logfile = "log.txt"

    try:
        # Sending HTTP GET request to the specified URL
        response = requests.get(url)
        status_code = response.status_code
        response_counts["total"] += 1

        # Logging the response code with timestamp to the log file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(logfile, "a") as file:
            file.write(f"{timestamp} - Response code for {url}: {status_code}\n")
            print(f"{timestamp} - Response code for {url}: {status_code}")

        # Check if response code doesn't start with '2'
        if str(status_code)[0] != '2':
            response_counts["non_200"] += 1
            # Check if it's time to send a notification (once per 30 minutes)
            if status_code not in last_notification_time or \
                    datetime.now() - last_notification_time[status_code] >= timedelta(minutes=30):
                # Send a push notification
                send(API_KEY, f"Non-2xx response: {status_code}", f"Response code for {url}: {status_code}")
                last_notification_time[status_code] = datetime.now()
                print("Push notification sent.")

    except requests.RequestException as e:
        # Handling request exceptions
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(logfile, "a") as file:
            file.write(f"{timestamp} - Error accessing {url}: {str(e)}\n")
            print(f"{timestamp} - Error accessing {url}: {str(e)}")


def daily_report():
    # Send a push notification with the count of non-200 responses out of total responses once per day
    print("running daily report")
    print("Total responses: ", response_counts["total"])
    print("API Key: ", API_KEY)
    if response_counts["total"] > 0:
        non_200_count = response_counts["non_200"]
        total_count = response_counts["total"]
        uptime = 100 * (1 - non_200_count / total_count)
        uptime_formatted = '{:.5f}'.format(uptime)
        message = f"{non_200_count} failures received out of {total_count} resulting in {uptime_formatted}% uptime."
        send(API_KEY, message)
        print("Sent ", message, " to api")
        # Reset counts for the next day
        response_counts["total"] = 0
        response_counts["non_200"] = 0




def main():
    # Schedule the send_get_request function to run every 1 minute
    schedule.every(1).minutes.do(send_get_request)
    # Schedule the daily_report function to run every day at midnight
    schedule.every().day.at("07:45").do(daily_report)

    while True:
        # Run pending scheduled tasks
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
