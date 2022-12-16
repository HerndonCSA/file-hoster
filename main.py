import mimetypes

from sanic import Sanic
from sanic import response
import aiofiles
import os

app = Sanic(__name__)

# create an in-memory cache to store the file data
cache = {}


async def get_file_data(file_path):
    # check if the file data is already in the cache
    if file_path in cache:
        return cache[file_path]
    # if the file data is not in the cache, read it from the file and store it in the cache
    async with aiofiles.open(file_path, "rb") as f:
        data = await f.read()
        cache[file_path] = data
        return data


@app.route("/upload", methods=["POST"])
async def upload_file(request):
    # get the file from the request
    file = request.files.get("file")

    # create the /files directory if it doesn't exist
    if not os.path.exists("files"):
        os.makedirs("files")

    # save the file to the /files directory using aiofiles
    file_path = os.path.join("files", file.name)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file.body)

    # return a JSON response indicating that the file was successfully uploaded
    return response.json({"success": True})


@app.route("/view/<file_name>")
async def view_file(request, file_name):
    # check if the "embed" query parameter is set to "true"
    embed = request.args.get("embed", "false") == "true"
    # get the file from the /files directory
    file_path = os.path.join("files", file_name)
    # get the file data from the cache or from the file
    file_data = await get_file_data(file_path)
    # determine the MIME type of the file based on its extension
    content_type, _ = mimetypes.guess_type(file_path)
    # set the Content-Type header to the determined MIME type
    headers = {"Content-Type": content_type}
    # if the "embed" query parameter is set to "true", return the file data as HTML with meta tags
    if embed:
        image_url = request.url.replace("?embed=true", "")
        # to embed on discord and twitter, send html response with meta tags
        # to link to the file, use the /view/<file_name> endpoint without the "embed" query parameter
        return response.html(
            f"""
            <html>
                <head>
                    <meta property="og:title" content="{image_url}" />
                    <meta name="twitter:image:src" content="{image_url}" />
                </head>
                <body>
                    <img src="{image_url}" />
                </body>
            </html>
            """
        )
    # if the "embed" query parameter is not set or is set to "false", return the file data as a response
    return response.raw(file_data, headers=headers)


@app.route("/files")
async def list_files(request):
    # get the list of filenames from the /files directory
    filenames = os.listdir("files")
    # return the list of filenames as a JSON response
    return response.json({"files": filenames})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
