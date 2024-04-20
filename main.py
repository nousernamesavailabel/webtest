import tkinter as tk
import requests
import schedule
import threading
import time
from datetime import datetime, timedelta
import simplepush

url = "https://webpt.com"
API_KEY = "Webpt100"

# Dictionary to store last notification time for each response status
last_notification_time = {}
# Dictionary to store response code counts
response_counts = {"total": 0, "non_200": 0}

def send_get_request():
    global response_counts, last_notification_time
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
                simplepush.send(API_KEY, f"Non-2xx response: {status_code}", f"Response code for {url}: {status_code}")
                last_notification_time[status_code] = datetime.now()
                print("Push notification sent.")

    except requests.RequestException as e:
        # Handling request exceptions
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(logfile, "a") as file:
            file.write(f"{timestamp} - Error accessing {url}: {str(e)}\n")
            print(f"{timestamp} - Error accessing {url}: {str(e)}")

def daily_report():
    global response_counts
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
        simplepush.send(API_KEY, message)
        print("Sent ", message, " to api")
        # Reset counts for the next day
        response_counts["total"] = 0
        response_counts["non_200"] = 0

def update_gui():
    # Function to update the GUI
    root.update()  # Update the Tkinter window
    root.after(1000, update_gui)  # Schedule next update after 1000 milliseconds
    total_label.config(text=f"Total Responses: {response_counts['total']}")
    non_200_label.config(text=f"Non-200 Responses: {response_counts['non_200']}")

def schedule_tasks():
    #send immediately
    send_get_request()

    # Schedule the send_get_request function to run every 1 minute
    schedule.every(1).minutes.do(send_get_request)
    # Schedule the daily_report function to run every day at midnight
    schedule.every().day.at("07:45").do(daily_report)

def run_scheduler():
    # Start the scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(1)

def send_test_notification():
    #message = "API Test"
    daily_report()

def main():
    global root, total_label, non_200_label
    root = tk.Tk()
    root.title("WebTest")

    label_text = ("WebTest Running: " + url)
    label = tk.Label(root, text=label_text, width=35)
    label.pack()

    total_label = tk.Label(root, text="Total Responses: 0")
    total_label.pack()

    non_200_label = tk.Label(root, text="Non-200 Responses: 0")
    non_200_label.pack()

    test_button = tk.Button(root, text="Test API", command=send_test_notification)
    test_button.pack()

    # Bind the window closing event to on_closing function
    root.protocol("WM_DELETE_WINDOW", root.quit)

    # Start threading for scheduler
    threading.Thread(target=run_scheduler, daemon=True).start()

    # Start updating the GUI
    update_gui()

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    # Perform initial scheduling of tasks
    schedule_tasks()
    main()
