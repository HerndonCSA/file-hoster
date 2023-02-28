import mimetypes
import shutil

from sanic import Sanic
from sanic import response
import aiofiles
import os
import aiosqlite
import uuid
import subprocess

from sanic_cors import CORS

app = Sanic(__name__)
CORS(app)
IMAGE_FILE_TYPES = [
    ".avif",
    ".bmp",
    ".gif",
    ".ief",
    ".jpg",
    ".jpe",
    ".jpeg",
    ".heic",
    ".heif",
    ".png",
    ".svg",
    ".tiff",
    ".tif",
    ".ico",
    ".ras",
    ".pnm",
    ".pbm",
    ".pgm",
    ".ppm",
    ".rgb",
    ".xbm",
    ".xpm",
    ".xwd"
]

VIDEO_FILE_TYPES = [
    ".mp4",
    ".m4v",
    ".mov",
    ".webm"
]

@app.listener('before_server_start')
async def init(application, loop):
    application.ctx.db = await aiosqlite.connect('file_index.db', loop=loop)
    await app.ctx.db.execute('''
        CREATE TABLE IF NOT EXISTS file_index (
            name TEXT,
            id TEXT,
            preview TEXT
        )
    ''')
    await application.ctx.db.commit()


@app.listener('after_server_stop')
async def close(application, _):
    await application.ctx.db.close()


app.register_listener(init, 'before_server_start')
app.register_listener(close, 'after_server_stop')


@app.route("/upload", methods=["POST", "GET"])
async def upload_file(request):
    # get the file from the request
    file = request.files.get("file")
    file_name = uuid.uuid4().hex
    # path of file will be uuid and extension
    file_path = os.path.join("files", file_name + mimetypes.guess_extension(file.type))
    if not os.path.exists("files"):
        os.makedirs("files")

    # save the file to the /files directory using aiofiles
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file.body)

    # if the file is a video, create a preview image
    if mimetypes.guess_type(file_path)[0].startswith('video'):
        subprocess.run(['ffmpeg', '-i', file_path, '-ss', '00:00:01.000', '-vframes', '1', file_path + '.jpg'])
        await app.ctx.db.execute('''
            INSERT INTO file_index (name, id, preview) VALUES (?, ?, ?)
        ''', (file.name, file_path.replace('files/', ''), file_path.replace('files/', '') + '.jpg'))
    else:
        await app.ctx.db.execute('''
            INSERT INTO file_index (name, id) VALUES (?, ?)
        ''', (file.name, file_path.replace('files/', '')))
    await app.ctx.db.commit()

    # return a JSON response indicating that the file was successfully uploaded, and a list of all files from the
    # database
    files = await app.ctx.db.execute('''
        SELECT * FROM file_index
    ''')
    files = await files.fetchall()
    return response.json({"success": True, "files": [{"id": file[1], "name": file[0]} for file in files]})


@app.route("/view/<file_name>")
async def view_file(request, file_name):
    # remove %20 from file_name
    file_name = file_name.replace("%20", " ")
    # check if the "embed" query parameter is set to "true"
    embed = request.args.get("embed", "false") == "true"
    preview = request.args.get("preview", "false") == "true"

    # get from database
    file = await app.ctx.db.execute('''
        SELECT * FROM file_index WHERE id = ?
    ''', (file_name,))
    file = await file.fetchone()
    if file is None:
        return response.json({"success": False, "error": "File not found"})
    if preview:
        if file[2] is None:
            # this file type does not have a preview, as it is not a video
            # if the file is an image, return the image, otherwise return a question mark image

            if not any(file[1].endswith(extension) for extension in IMAGE_FILE_TYPES):
                return await response.file_stream("./unknown.png")
            else:
                return await response.file_stream(os.path.join("files", file[1]))
        else:
            file_name = file[2]
    else:
        file_name = file[1]
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
                        <meta property="og:title" content="{file[0]}" />
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
                        <meta name="twitter:title" content="{file[0]}">
                        <meta name="twitter:card" content="summary_large_image">
                        <meta property="og:title" content="{file[0]}" />
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
    # # delete the file from the /files directory
    # # remove %20 from file_name
    # file_name = file_name.replace("%20", " ")
    # os.remove("files/" + file_name)
    #
    # # return a JSON response indicating that the file was successfully deleted
    # files = os.listdir("files")
    # return response.json({"success": True, "files": files})

    # get the file from the database
    file = await app.ctx.db.execute('''
        SELECT * FROM file_index WHERE id = ?
    ''', (file_name,))
    file = await file.fetchone()
    if file is None:
        return response.json({"success": False, "error": "File not found"})
    # delete the file from the /files directory
    os.remove("files/" + file[1])
    if file[2] is not None:
        os.remove("files/" + file[2])
    # delete the file from the database
    await app.ctx.db.execute('''
        DELETE FROM file_index WHERE id = ?
    ''', (file_name,))
    await app.ctx.db.commit()
    # return a JSON response indicating that the file was successfully deleted
    files = await app.ctx.db.execute('''
        SELECT * FROM file_index
    ''')
    files = await files.fetchall()
    return response.json({"success": True, "files": [{"id": file[1], "name": file[0]} for file in files]})


@app.route("/files")
async def list_files(request):
    # # get the list of filenames from the /files directory
    # filenames = os.listdir("files")
    # # return the list of filenames as a JSON response
    # return response.json({"files": filenames})

    # get the list of filenames from the database
    files = await app.ctx.db.execute('''
        SELECT * FROM file_index
    ''')
    files = await files.fetchall()
    # return the list of filenames as a JSON response
    return response.json({"files": [{"id": file[1], "name": file[0]} for file in files]})

@app.route("/supported-image-types")
async def image_file_types(request):
    return response.json({"image_file_types": IMAGE_FILE_TYPES})

@app.route("/supported-video-types")
async def video_file_types(request):
    return response.json({"video_file_types": VIDEO_FILE_TYPES})

@app.route("/storage")
async def storage(request):
    # get the total storage space
    total, used, free = shutil.disk_usage("/")
    # return the storage space as a JSON response
    return response.json({"total": total, "used": used, "free": free}) # these values are in bytes

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
