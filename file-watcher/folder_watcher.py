import subprocess
import pathlib
import os
import aiohttp

from watchdog.events import FileSystemEventHandler
import asyncio
from pync import Notifier


async def catch_all_handler(event, api_url):
    dest_path = event.dest_path
    if not os.path.exists(dest_path):
        return

    try:
        async with aiohttp.ClientSession() as session:
            # open the file you want to upload
            with open(dest_path, "rb") as f:
                file_data = f.read()

            # create the form data object with the file field and file data
            form_data = aiohttp.FormData()
            form_data.add_field("file", file_data, filename=pathlib.Path(dest_path).name)
            print("File name: " + pathlib.Path(dest_path).name)

            # make the POST request to the /upload route
            async with session.post(api_url + "/upload", data=form_data) as resp:
                data = await resp.json()
                url = f"{api_url}/view/" + data['uploaded-file-id'] + "?embed=true"
                subprocess.run("pbcopy", text=True, input=url)
                Notifier.notify('File Embed copied to clipboard', open=url)
    except Exception as e:
        print(e)
        print('error')


async def handle_video(path, api_url):
    async with aiohttp.ClientSession() as session:
        # open the file you want to upload
        with open(path, "rb") as f:
            file_data = f.read()

        # create the form data object with the file field and file data
        form_data = aiohttp.FormData()
        form_data.add_field("file", file_data, filename=pathlib.Path(path).name)

        async with session.post(api_url + "/upload", data=form_data) as resp:
            data = await resp.json()
            url = f"{api_url}/view/" + data['uploaded-file-id'] + "?embed=true"
            subprocess.run("pbcopy", text=True, input=url)
            Notifier.notify('File Embed copied to clipboard', open=url)


class FolderChangeHandler(FileSystemEventHandler):

    def __init__(self, api_url):
        self.api_url = api_url
        super().__init__()

    # on macos, on_moved is called when a screenshot is taken
    def on_moved(self, event):
        # call async function
        asyncio.run(catch_all_handler(event, self.api_url))

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
            asyncio.run(handle_video(path_, self.api_url))
            # delete the mov file
            os.remove(event.src_path)

    def on_any_event(self, event):
        pass
