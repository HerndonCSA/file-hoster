import { useEffect, useState } from 'react'
import Button from '@mui/material/Button';
import DeleteIcon from './assets/delete.svg'
import DownloadIcon from './assets/download.svg'
import PlayIcon from './assets/play.svg'

// import motion from 'framer-motion'
import { motion, AnimatePresence } from 'framer-motion'


const API_URL = 'http://localhost:8000'


function App() {
    const [files, setFiles] = useState([])
    const [largeView, setLargeView] = useState(false)
    const [largeViewImage, setLargeViewImage] = useState("");
    const [supportedImageTypes, setSupportedImageTypes] = useState([]);
    const [supportedVideoTypes, setSupportedVideoTypes] = useState([]);

    useEffect(() => {
        fetch(`${API_URL}/supported-image-types`)
            .then(response => response.json())
            .then(data => {
                console.log(data)
                setSupportedImageTypes(data['image_file_types'])
            })

        fetch(`${API_URL}/supported-video-types`)
            .then(response => response.json())
            .then(data => {
                console.log(data)
                setSupportedVideoTypes(data['video_file_types'])
            }
            )
    }, [])


    const downloadFile = (file) => {
        fetch(`${API_URL}/view/${file}`)
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.style.display = 'none'
                // set the href to the blob url
                a.href = url
                // set the download attribute to the file name
                a.setAttribute('download', file)
                // append the anchor tag to the body
                document.body.appendChild(a)
                // click the anchor tag to download the file
                a.click()
                // remove the anchor tag from the body
                document.body.removeChild(a)
            })
    }

    const deleteFile = (file) => {
        console.log("deleting file" + file)
        fetch(`${API_URL}/delete/${file}`, {
            method: 'DELETE'
        })
            .then(response => response.json())
            .then(data => {
                console.log(data)
                setFiles(data['files'])
                console.log("deleted file " + file + " " + (data["files"].includes(file) === false))
            })
    }


    const uploadFile = () => {
        // upload images from clients file system
        const input = document.createElement('input')
        // only allow images
        input.setAttribute('type', 'file')
        input.type = 'file'
        input.multiple = true
        input.onchange = e => {
            const files = e.target.files
            for (let i = 0; i < files.length; i++) {
                const formData = new FormData()
                formData.append('file', files[i])
                fetch(`${API_URL}/upload`, {
                    method: 'POST', body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        console.log(data)
                        setFiles(data['files'])
                    })
            }
        }
        input.click()
    }


    useEffect(() => {
        fetch(`${API_URL}/files`)
            .then(response => response.json())
            .then(data => {
                console.log(data['files'])
                setFiles(data['files'])
            })
    }, [])

    useEffect(() => {
        console.log("adding event listeners")
        const handleDrop = e => {
            e.preventDefault()
            const file = e.dataTransfer.files
            for (let i = 0; i < file.length; i++) {
                const formData = new FormData()
                formData.append('file', file[i])
                fetch(`${API_URL}/upload`, {
                    method: 'POST', body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        console.log(data)
                        setFiles(data['files'])
                    })
            }
        }

        const handleDragOver = e => {
            e.preventDefault()
        }

        document.getElementById("root").addEventListener('drop', handleDrop)
        document.getElementById("root").addEventListener('dragover', handleDragOver)

        return () => {
            document.getElementById("root").removeEventListener('drop', handleDrop)
            document.getElementById("root").removeEventListener('dragover', handleDragOver)
        }
    }, [])




    return (
        <>
            <AnimatePresence>
                {
                    largeView ?
                        <motion.div className="large-view" key="large-view"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            {
                                supportedImageTypes.includes(largeViewImage.split('.').pop()) ?
                                    <img src={largeViewImage} alt="large view" onClick={() => {
                                        // enable scrolling
                                        document.body.style.overflow = "auto"
                                        setLargeView(false)
                                    }
                                    } />
                                    :
                                    <video controls src={largeViewImage} alt="large view" onClick={() => {
                                        // enable scrolling
                                        document.body.style.overflow = "auto"
                                        setLargeView(false)
                                    }
                                    } />
                            }
                        </motion.div>
                        : null
                }
            </AnimatePresence>
            <div className="header">
                <h1>Drag a file</h1>
                <h2>or</h2>
                <Button className="upload" variant='contained'
                    onClick={uploadFile}
                >UPLOAD
                </Button>
            </div>
            <div className="files">
                {files.map(file => {
                    // console log if the file is a video 
                    return (
                        <div className="file" key={file["id"]}>
                            <div className="image" onClick={() => {
                                // scroll to top
                                window.scrollTo(0, 0)
                                // disable scrolling
                                document.body.style.overflow = "hidden"
                                setLargeView(true)
                                setLargeViewImage(`${API_URL}/view/${file["id"]}`)
                            }}>
                                {/* if the file is a video, add a play button */}
                                {supportedVideoTypes.includes("." + file["name"].split('.').pop()) ? <img src={PlayIcon} alt="play" /> : null}
                                <img src={`${API_URL}/view/${file["id"]}?preview=true`} alt={file} />
                            </div>
                            <div className="controls">
                                <p>{file["name"].length > 15 ? file["name"].substring(0, 15) + "..." : file["name"]}</p>
                                <Button>
                                    <img src={DownloadIcon} alt="Download" onClick={() => downloadFile(file["id"])} />
                                </Button>
                                <Button>
                                    <img src={DeleteIcon} alt="Delete" onClick={() => deleteFile(file["id"])} />
                                </Button>
                                <Button
                                    onClick={() => {
                                        console.log(supportedImageTypes)
                                        navigator.clipboard.writeText(`${API_URL}/view/${file["id"]}?embed=true`)
                                    }}
                                >
                                    Embed
                                </Button>
                            </div>
                        </div>
                    )
                })}



            </div>
        </>)
}


export default App
