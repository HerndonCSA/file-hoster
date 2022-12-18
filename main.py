import mimetypes

from sanic import Sanic
from sanic import response
import aiofiles
import os

import subprocess

from sanic_cors import CORS

app = Sanic(__name__)
CORS(app)



@app.route("/upload", methods=["POST", "GET"])
async def upload_file(request):
    print(request.files)
    # get the file from the request
    file = request.files.get("file")

    # create the /files directory if it doesn't exist
    if not os.path.exists("files"):
        os.makedirs("files")

    # save the file to the /files directory using aiofiles
    file_path = os.path.join("files", file.name.replace('%20', ' '))
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file.body)

    # return a JSON response indicating that the file was successfully uploaded
    files = os.listdir("files")
    return response.json({"success": True, "files": files})


@app.route("/view/<file_name>")
async def view_file(request, file_name):
    # remove %20 from file_name
    file_name = file_name.replace("%20", " ")
    # check if the "embed" query parameter is set to "true"
    embed = request.args.get("embed", "false") == "true"
    if embed:
        image_url = request.url.replace("?embed=true", "")
        # to embed on discord and twitter, send html response with meta tags
        # to link to the file, use the /view/<file_name> endpoint without the "embed" query parameter

        # if .png, .jpg, or .jpeg, use <meta property="og:image" content="https://example.com/image.png">
        if file_name.endswith(('.png', '.jpg', '.jpeg')):
            return response.html(
                f"""
                        <html>
                            <head>
                                <meta content="File Hoster v2" property="og:site_name">
                                <meta property="og:title" content="{file_name}" />
                                <meta property="og:image" content="{image_url}" />
                                <meta name="twitter:card" content="summary_large_image">
                            </head>
                            <body>
                                <img src="{image_url}" />
                            </body>
                        </html>
                        """
            )
        # if .mp4, .mov, or .webm, use <meta property="og:video" content="https://example.com/video.mp4">
        elif file_name.endswith(('.mp4', '.mov', '.webm')):
            return response.html(
                f"""
                        <html>
                            <head>
                <meta name="twitter:title" content="{file_name}">
                <meta name="twitter:card" content="summary_large_image">
                <meta property="og:video:url" content="{image_url}">
                <meta property="og:video:height" content="720">
                <meta property="og:video:width" content="1280">
                <meta property="og:type" content="video.other">
                            </head>
                            <body>
                                <video controls src="{image_url}" />
                            </body>
                        </html>
                        """
            )
    # if the "embed" query parameter is not set or is set to "false", return the file data as a response
    return await response.file_stream("files/" + file_name)


@app.route("/delete/<file_name>", methods=["DELETE"])
async def delete_file(request, file_name):
    # delete the file from the /files directory
    os.remove("files/" + file_name)

    # return a JSON response indicating that the file was successfully deleted
    files = os.listdir("files")
    return response.json({"success": True, "files": files})


@app.route("/files")
async def list_files(request):
    # get the list of filenames from the /files directory
    filenames = os.listdir("files")
    # return the list of filenames as a JSON response
    return response.json({"files": filenames})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
