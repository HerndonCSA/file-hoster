import subprocess
import time
import requests
import pathlib
import os
import aiohttp

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import asyncio
from pync import Notifier

ngrok = "https://4fd0-71-127-36-141.ngrok.io"


async def catch_all_handler(event):
    dest_path = event.dest_path
    print(dest_path)
    if not os.path.exists(dest_path):
        print('file does not exist')
        return

    try:
        # subprocess.call(["open", "-R", dest_path])
        print(pathlib.Path(dest_path).name + ' exists')
        # get request using aiohttp to localhost:8000/files
        async with aiohttp.ClientSession() as session:
            # open the file you want to upload
            with open(dest_path, "rb") as f:
                file_data = f.read()

            # create the form data object with the file field and file data
            form_data = aiohttp.FormData()
            form_data.add_field("file", file_data, filename=pathlib.Path(dest_path).name)

            # make the POST request to the /upload route
            async with session.post("http://localhost:8000/upload", data=form_data) as resp:
                print(await resp.text())
                url = f"{ngrok}/view/" + pathlib.Path(dest_path).name.replace(' ',
                                                                              '%20') + "?embed=true"
                subprocess.run("pbcopy", text=True, input=url)
                Notifier.notify('File Embed copied to clipboard', open=url)
    except Exception as e:
        print(e)
        print('error')


async def handle_video(path):
    async with aiohttp.ClientSession() as session:
        # open the file you want to upload
        with open(path, "rb") as f:
            file_data = f.read()

        # create the form data object with the file field and file data
        form_data = aiohttp.FormData()
        form_data.add_field("file", file_data, filename=pathlib.Path(path).name)

        async with session.post("http://localhost:8000/upload", data=form_data) as resp:
            print(await resp.text())
            url = f"{ngrok}/view/" + pathlib.Path(path).name.replace(' ', '%20') + "?embed=true"
            subprocess.run("pbcopy", text=True, input=url)
            Notifier.notify('File Embed copied to clipboard', open=url)


class MyEventHandler(FileSystemEventHandler):
    def on_moved(self, event):
        # call async function
        asyncio.run(catch_all_handler(event))

    def on_created(self, event):
        # if the file is a mov file
        if pathlib.Path(event.src_path).suffix == '.mov':
            # call async function
            # convert the file to mp4

            subprocess.run(
                ['ffmpeg', '-i', event.src_path, '-c:v', 'libx264', '-crf', '23', '-preset', 'medium', '-c:a', 'aac',
                 '-b:a', '128k', '-movflags', '+faststart', '-vf', 'scale=1280:-2', '-y',
                 event.src_path.replace('.mov', '.mp4')])
            path_ = pathlib.Path(event.src_path.replace('.mov', '.mp4'))
            asyncio.run(handle_video(path_))

    def on_any_event(self, event):
        print(event)


path = '/Users/soos/Desktop/Screenshots'

event_handler = MyEventHandler()
observer = Observer()
observer.schedule(event_handler, path, recursive=True)
observer.start()
print(f'-- WATCHER V1.0 WATCHING {path} --')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
