import subprocess
import pathlib
import os
import platform
import asyncio
import aiohttp
import pyperclip  # Import pyperclip for cross-platform clipboard operations

from watchdog.events import FileSystemEventHandler

# Conditionally import and set up notification based on the OS
if platform.system() == 'Darwin':  # macOS
    from pync import Notifier


    def notify(url):
        Notifier.notify('File Embed copied to clipboard', title='Quick Embed', open=url)
elif platform.system() == 'Windows':  # Windows
    from plyer import notification


    def notify(url):
        notification.notify(title='Quick Embed', message='File Embed copied to clipboard',
                            timeout=10, ticker='Quick Embed', toast=False, app_name='Quick Embed',
                            callback_on_click=url)
else:
    def notify(title, message, open=None):
        print(f"Notification: {title} - {message}")


async def catch_all_handler(event, api_url):
    dest_path = event.dest_path
    if not os.path.exists(dest_path):
        print("Fuck")
        return

    async with aiohttp.ClientSession() as session:
        with open(dest_path, "rb") as f:
            file_data = f.read()
        print("AAA:")
        print(len(file_data))

        form_data = aiohttp.FormData()
        form_data.add_field("file", file_data, filename=pathlib.Path(dest_path).name)

        async with session.post(api_url + "/upload", data=form_data) as resp:
            data = await resp.json()
            url = f"{api_url}/view/" + data['uploaded-file-id'] + "?embed=true"
            pyperclip.copy(url)  # Use pyperclip to copy URL to clipboard
            notify(url)


async def handle_video(path, api_url):
    async with aiohttp.ClientSession() as session:
        with open(path, "rb") as f:
            file_data = f.read()

        form_data = aiohttp.FormData()
        form_data.add_field("file", file_data, filename=pathlib.Path(path).name)

        async with session.post(api_url + "/upload", data=form_data) as resp:
            data = await resp.json()
            url = f"{api_url}/view/" + data['uploaded-file-id'] + "?embed=true"
            pyperclip.copy(url)  # Use pyperclip to copy URL to clipboard
            notify(url)


class FolderChangeHandler(FileSystemEventHandler):

    def __init__(self, api_url):
        self.api_url = api_url
        super().__init__()

    def on_moved(self, event):
        asyncio.run(catch_all_handler(event, self.api_url))

    def on_created(self, event):
        print("hello")
        if pathlib.Path(event.src_path).suffix == '.mov':
            subprocess.run(
                ['ffmpeg', '-i', event.src_path, '-c:v', 'libx264', '-crf', '23', '-preset', 'medium', '-c:a', 'aac',
                 '-b:a', '128k', '-movflags', '+faststart', '-vf', 'scale=1280:-2', '-y',
                 event.src_path.replace('.mov', '.mp4')])
            path_ = pathlib.Path(event.src_path.replace('.mov', '.mp4'))
            asyncio.run(handle_video(path_, self.api_url))
            os.remove(event.src_path)

        elif platform.system() == 'Windows':
            event.dest_path = event.src_path
            print(event.src_path)
            asyncio.run(catch_all_handler(event, self.api_url))

    def on_any_event(self, event):
        pass
