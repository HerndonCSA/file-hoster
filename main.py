from sanic import Sanic
from sanic.response import json, text, redirect
from sanic.response import html as html_response
import base64
import os
import aiofiles

app = Sanic(__name__)

# dictionary to store uploaded files
files = {}

@app.route("/", methods=["POST"])
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

    # redirect to the GET / route
    return redirect("/")

@app.route("/", methods=["GET"])
async def browse_files(request):
    # get the list of filenames from the /files directory
    filenames = os.listdir("files")
    # filter the list of filenames to include only image files
    image_filenames = [f for f in filenames if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg")]

    # create the HTML for displaying the image files
    html = "<html><head><style>img { max-width: 10em; max-height: 10em; min-width: 10em; max-width: 10em; }</style></head><body>"
    # add a form to the HTML that allows users to upload files
    html += "<form method='POST' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.png, .jpg, .jpeg'>"
    html += "<input type='submit' value='Upload'>"
    html += "</form>"
    # add a form to the HTML that allows users to delete all files
    html += "<form method='POST' action='/delete'>"
    html += "<input type='submit' value='Delete All Files'>"
    html += "</form>"
    for filename in image_filenames:
        # create an <img> tag for each image file
        img_tag = "<img src='data:image/png;base64,{}' alt='{}'>"
        # import the base64 module
        # encode the file content as base64 using aiofiles
        file_path = os.path.join("files", filename)
        async with aiofiles.open(file_path, "rb") as f:
            file_content = base64.b64encode(await f.read()).decode("utf-8")
        # format the img tag with the base64-encoded file content and the filename
        img_tag = img_tag.format(file_content, filename)
        # add the img tag to the HTML
        html += img_tag
    html += "</body></html>"

    # return the HTML as the response
    return html_response(html)

@app.route("/delete", methods=["POST"])
async def delete_files(request):
    # get the list of filenames from the /files directory
    filenames = os.listdir("files")

    # delete all files in the /files directory
    for filename in filenames:
        file_path = os.path.join("files", filename)
        os.remove(file_path)

    # redirect to the GET / route
    return redirect("/")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)