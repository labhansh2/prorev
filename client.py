import tkinter as tk
import pathlib
import webbrowser
from PIL import Image, ImageTk
import subprocess
import os
import sys
import signal
import psutil
import time
from notion_client import Client
from notion_client import errors
import requests

from prorev import data

conn = False


def get_connection_info():

    # also handle for multiple connections
    connection = data.get_connection()
    if not connection or len(connection) == 0:
        return False
    else:
        return {
            "integration_token": connection[0][0],
            "page_name": connection[0][1],
            "process_id": connection[0][2],
            "notif_channel": connection[0][3]
        }


def start_main():
    global conn
    conn = get_connection_info()

    if hasattr(sys, "_MEIPASS"):
        # command for the executable
        command = ['./main.exe', '--debug']
    else:
        # command for the script
        command = ['python', 'main.py', '--debug']

    if sys.platform.startswith('win'):
        # Windows
        # Check if the background process is not already running
        if conn['process_id'] == '':
            main_bgp = subprocess.Popen(
                command,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print(str(main_bgp.pid) + ' process started')
            return main_bgp.pid

        # can't use or coz when pid == '', it can't be an int
        elif not int(conn['process_id']) in (p.pid for p in psutil.process_iter()):
            main_bgp = subprocess.Popen(
                command,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print(str(main_bgp.pid) + ' process started')
            return main_bgp.pid
    else:
        # Linux/macOS
        if not os.path.exists('/proc/' + str(conn['process_id'])):
            main_bgp = subprocess.Popen(
                command,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return main_bgp.pid

    return False


def stop_main(pid):

    # Check if the background process is running
    if pid is not None:
        if sys.platform.startswith('win'):
            # Windows platform
            subprocess.run(
                ['taskkill', '/PID', str(pid), '/F'], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Linux/macOS platform
            os.kill(pid, signal.SIGTERM)


def verify_token_and_page(token, page_name):
    try:
        notion = Client(auth=token)
        target_page = notion.search(
            query=page_name, **{
                "object": "page"
            }
        )
        page_id = target_page['results'][0]['id']
    except errors.APIResponseError as e:
        return False, 7
    except IndexError as i:
        return False, 8
    else:
        return True, 0


def is_running(pid):
    if pid != "" and int(pid) in (p.pid for p in psutil.process_iter()):
        return True
    else:
        return False


def check_internet_connection():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


class ProRevClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("400x300")
        self.title("Pro Rev Client")
        logo_path = pathlib.Path(__file__).parent/"img/"
        self.iconbitmap(logo_path/"icon.ico")

        self.frames = {}

        self.create_frame(1, "Add New Connection")
        self.create_frame(2, "Try Again (Add New Connection)")
        self.create_frame(3, "Active")
        self.create_frame(4, "Not Active")
        # self.create_frame(5, "Notification Info")
        self.create_frame(6, "Loading")
        self.create_frame(7, 'API Token Not Found')
        self.create_frame(8, 'Page Not Found')
        self.create_frame(9, 'No Internet Connection')

        data.create_connection_table()
        connection_info = get_connection_info()
        if connection_info:
            process_id = connection_info['process_id']
            if is_running(process_id):
                frame_no = 3
            else:
                frame_no = 4
        else:
            frame_no = 1

        if not check_internet_connection():
            frame_no = 9

        self.show_frame(frame_no)  # Show the first frame initially

    def create_frame(self, frame_number, title):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        self.frames[frame_number] = frame

        if frame_number == 1:
            # Frame 1: Add New Connection
            tk.Label(frame, text="Create a New Connection", font=(
                "Arial", 12)).pack(pady=10)
            integration_token_entry = tk.Entry(
                frame, font=("Arial", 12), justify=tk.CENTER, width=38)
            integration_token_entry.insert(tk.END, "Integration Token")
            integration_token_entry.pack(pady=10)

            page_name_entry = tk.Entry(
                frame, font=("Arial", 12), justify=tk.CENTER)
            page_name_entry.insert(tk.END, "Page Name")
            page_name_entry.pack(pady=10)

            start_button = tk.Button(
                frame, text="Start", command=self.start_new_connection)
            start_button.pack(pady=10)

            help_button = tk.Button(
                frame, text="Help", command=self.view_help)
            help_button.pack()

        elif frame_number == 2:
            # Frame 2: Try Again (Add New Connection)
            tk.Label(frame, text="Try again [ refer help ]", font=(
                "Arial", 12)).pack(pady=10)

            integration_token_entry = tk.Entry(
                frame, font=("Arial", 12), justify=tk.CENTER, width=38)
            integration_token_entry.insert(tk.END, "Integration Token")
            integration_token_entry.pack(pady=10)

            page_name_entry = tk.Entry(
                frame, font=("Arial", 12), justify=tk.CENTER)
            page_name_entry.insert(tk.END, "Page Name")
            page_name_entry.pack(pady=10)

            start_button = tk.Button(
                frame, text="Start", command=self.start_new_connection)
            start_button.pack(pady=10)

            help_button = tk.Button(
                frame, text="Help", command=self.view_help)
            help_button.pack()

        elif frame_number == 3:
            # Frame 3: Active
            tk.Label(frame, text="Connection is active",
                     font=("Arial", 14)).pack(pady=10)

            image_path = pathlib.Path(__file__).parent/"img/"
            image = Image.open(image_path/"on.png")
            image = image.resize((40, 40))
            photo = ImageTk.PhotoImage(image)

            image_label = tk.Label(frame, image=photo)
            image_label.image = photo
            image_label.pack()

            stop_button = tk.Button(
                frame, text="Stop", command=self.deactivate)
            stop_button.pack(pady=10)

            get_notif_button = tk.Button(
                frame, text="Get Notifications", command=self.view_notif_info)
            get_notif_button.pack()

        elif frame_number == 4:
            # Frame 4: Not Active
            tk.Label(frame, text="Connection is not active",
                     font=("Arial", 14)).pack(pady=10)

            image_path = pathlib.Path(__file__).parent/"img/"
            image = Image.open(image_path/"off.png")
            image = image.resize((40, 40))
            photo = ImageTk.PhotoImage(image)

            image_label = tk.Label(frame, image=photo)
            image_label.image = photo  # Store a reference to prevent garbage collection
            image_label.pack()

            activate_button = tk.Button(
                frame, text="Activate", command=self.activate)
            activate_button.pack(pady=10)

            start_new_button = tk.Button(
                frame, text="Create New Connection", command=lambda: self.show_frame(1))
            start_new_button.pack()

        elif frame_number == 5:
            # Frame 5: Notification Info
            tk.Label(frame, text="Scan the QR to subscribe on other devices", font=(
                "Arial", 14)).pack(pady=10)

            # Load the image
            data.create_connection_table()
            db_conn = data.get_connection()

            notif_endpoint = None
            if len(db_conn) != 0:
                notif_endpoint = db_conn[0][3]

            if notif_endpoint:
                image_name = get_connection_info()['notif_channel'].replace(
                    "https://notify.run/", "") + '.png'

                if hasattr(sys, "_MEIPASS"):
                    # Running as executable
                    base_path = os.path.dirname(sys.executable)
                    path = os.path.join(base_path, "img")
                    image_path = pathlib.Path(path)
                    # print(image_path)
                else:
                    # Running as script
                    image_path = pathlib.Path(__file__).parent/"img/"

                image = Image.open(image_path/image_name)
                image = image.resize((140, 140))
                photo = ImageTk.PhotoImage(image)

                image_label = tk.Label(frame, image=photo)
                image_label.image = photo  # Store a reference to prevent garbage collection
                image_label.pack()

            subscribe_button = tk.Button(
                frame, text="Subscribe on this device", command=self.notif_redirect)
            subscribe_button.pack(pady=10)

            go_back_button = tk.Button(
                frame, text="Go Back", command=lambda: self.show_frame(3))
            go_back_button.pack()

        elif frame_number == 6:
            # Frame 6: Loading
            tk.Label(frame, text="Loading...", font=(
                "Arial", 14)).pack(pady=10)

        elif frame_number == 7:
            # Frame 7: API Token Invalid
            tk.Label(frame, text="Error : Integration token is not valid", font=(
                "Arial", 14)).pack(pady=10)

            try_again_button = tk.Button(
                frame, text="Try Again", command=lambda: self.show_frame(1))
            try_again_button.pack(pady=10)

            help_button = tk.Button(
                frame, text="Help", command=lambda: self.view_help())
            help_button.pack()

        elif frame_number == 8:
            # Frame 8: Page Not Found

            error_label = tk.Label(
                frame, text="Error: Page Not Found", font=("Arial", 16, "bold"))
            error_label.pack()

            reasons_label = tk.Label(
                frame, text="Following might be the reasons:", font=("Arial", 12))
            reasons_label.pack()

            reason1_label = tk.Label(
                frame, text="1. Entered Wrong Page Name", font=("Arial", 12))
            reason1_label.pack()

            reason2_label = tk.Label(
                frame, text="2. Page is not connected to the Notion Integration", font=("Arial", 12))
            reason2_label.pack()

            reason3_label = tk.Label(
                frame, text="3. No Such Page Exists For the User", font=("Arial", 12))
            reason3_label.pack()

            try_again_button2 = tk.Button(
                frame, text="Try Again", command=lambda: self.show_frame(1))
            try_again_button2.pack(pady=10)

            help_button2 = tk.Button(
                frame, text="Help", command=lambda: self.view_help())
            help_button2.pack()

        elif frame_number == 9:
            # Frame 9 : No Internet Connection

            error_label = tk.Label(
                frame, text="Error: No Internet Connection", font=("Arial", 16, "bold"))
            error_label.pack()

            reasons_label = tk.Label(
                frame, text="Close and Try Again", font=("Arial", 12))
            reasons_label.pack()

    def show_frame(self, frame_number):
        for frame in self.frames.values():
            frame.pack_forget()

        frame = self.frames[frame_number]
        frame.pack(fill=tk.BOTH, expand=True)

    def hide_frame(self, frame_number):
        frame = self.frames[frame_number]
        frame.pack_forget()

    def start_new_connection(self):
        if not check_internet_connection():
            self.show_frame(9)
        integration_token = self.frames[1].children['!entry'].get()
        page_name = self.frames[1].children['!entry2'].get()

        # not working
        if not integration_token and page_name:
            integration_token = self.frames[2].children['!entry'].get()
            page_name = self.frames[2].children['!entry2'].get()

        data.erase_connection()

        if integration_token and page_name:

            status, code = verify_token_and_page(integration_token, page_name)
            if status:
                data.add_connection(integration_token=integration_token,
                                    page_name=page_name,
                                    process_id='',
                                    notif_channel='')
                self.activate()

            else:
                self.show_frame(code)

    def deactivate(self):
        connection_info = get_connection_info()

        loading_frame = tk.Frame(self, padx=20, pady=20)
        loading_frame.pack()
        loading_label = tk.Label(
            loading_frame, text="Loading...", font=("Arial", 16, "bold"))
        loading_label.pack()

        self.update()

        pid = connection_info['process_id']
        stop_main(pid=pid)
        data.update_pid('', connection_info['integration_token'])

        loading_frame.pack_forget()

        self.show_frame(4)

    def activate(self):
        conn = get_connection_info()

        # add loading view in form of function decorator
        loading_frame = tk.Frame(self, padx=20, pady=20)
        loading_frame.pack()
        loading_label = tk.Label(
            loading_frame, text="Loading...", font=("Arial", 16, "bold"))
        loading_label.pack()

        self.update()

        pid = start_main()
        if pid:
            data.update_pid(pid, conn['integration_token'])
        # time.sleep(time_kill)

        loading_frame.pack_forget()

        self.show_frame(3)
        # here can run a loop or something to keep checking if the
        # process is running or not, if not, redirect to
        # inactive
        # or take necessary action

    def view_notif_info(self):
        self.create_frame(5, 'Notification Info')
        self.show_frame(5)

    def notif_redirect(self):
        connection = data.get_connection()
        webbrowser.open(connection[0][3])

    def view_help(self):
        # change this to the endpoint url logic
        webbrowser.open(
            'https://www.github.com/labhansh2/prorev#getting-started')


if __name__ == "__main__":
    app = ProRevClientGUI()
    app.mainloop()
