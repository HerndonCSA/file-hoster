import { useEffect, useState, useRef } from 'react'
import Button from '@mui/material/Button';
import DeleteIcon from './assets/delete.svg'
import DownloadIcon from './assets/download.svg'
import PlayIcon from './assets/play.svg'
import Nanobar from "nanobar";
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'


const API_URL = import.meta.env.VITE_API_URL;


function App() {
    const [files, setFiles] = useState([])
    const [largeView, setLargeView] = useState(false)
    const [largeViewFile, setLargeViewFile] = useState("");
    const [largeViewIsVideo, setLargeViewIsVideo] = useState(false)
    const [supportedImageTypes, setSupportedImageTypes] = useState([]);
    const [supportedVideoTypes, setSupportedVideoTypes] = useState([]);
    const [storageinfo, setStorageInfo] = useState({ "total": 0, "used": 0, "free": 0 });
    const larrgeViewFileRef = useRef(null);
    const playerRef = useRef(null);

    function bytesToGB(bytes) {
        return (bytes / 1024 / 1024 / 1024).toFixed(2);
    }


    const loading_bar = useRef();

    useEffect(() => {
        loading_bar.current = new Nanobar();
    }, [])


    useEffect(() => {
        // get storage info
        fetch(`${API_URL}/storage`)
            .then(response => response.json())
            .then(data => {
                console.log(data)
                setStorageInfo(data)
            })
    }, [])

    // use effect to create the player



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


    const downloadFile = (file_id, file_name) => {
        file_name.replace("%20", " ")
        fetch(`${API_URL}/view/${file_id}`)
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = file_name;
                a.click();
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
                setFiles(data['files'].reverse())
                console.log("deleted file " + file + " " + (data["files"].includes(file) === false))
            })
    }


    const convertToBase64 = (str) => {
        return btoa(
            encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function toSolidBytes(match, p1) {
                return String.fromCharCode('0x' + p1);
            })
        );
    }



    const uploadFile = () => {
        // upload images from clients file system
        const input = document.createElement('input');
        // only allow images
        input.setAttribute('type', 'file');
        input.type = 'file';
        input.multiple = true;
        input.onchange = e => {
            const files = e.target.files;
            for (let i = 0; i < files.length; i++) {
                const formData = new FormData();
                formData.append('file', files[i]);
                axios.post(`${API_URL}/upload`, formData, {
                    onUploadProgress: (progressEvent) => {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        console.log(percentCompleted);
                        loading_bar.current.go(percentCompleted);
                    }
                })
                    .then(response => {
                        console.log(response.data);
                        setFiles(response.data['files'].reverse());
                    })
                    .catch(error => {
                        console.log(error);
                    });
            }
        };
        input.click();
    };


    useEffect(() => {
        fetch(`${API_URL}/files`)
            .then(response => response.json())
            .then(data => {
                console.log(data['files'])
                setFiles(data['files'].reverse())
            })
    }, [])

    useEffect(() => {
        console.log("adding event listeners")
        const handleDrop = e => {
            e.preventDefault();
            const file = e.dataTransfer.files;
            for (let i = 0; i < file.length; i++) {
                const formData = new FormData();
                formData.append('file', file[i]);
                axios.post(`${API_URL}/upload`, formData, {
                    onUploadProgress: (progressEvent) => {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        console.log(percentCompleted);
                        loading_bar.current.go(percentCompleted);
                    }
                })
                    .then(response => {
                        console.log(response.data);
                        setFiles(response.data['files'].reverse());
                    })
                    .catch(error => {
                        console.log(error);
                    });
            }
        };
        const handleDragOver = e => {
            e.preventDefault()
        }

        document.body.addEventListener('drop', handleDrop)
        document.body.addEventListener('dragover', handleDragOver)

        return () => {
            window.removeEventListener('drop', handleDrop)
            window.removeEventListener('dragover', handleDragOver)
        }
    }, [])

    // escape to close large view
    useEffect(() => {
        const handleEscape = e => {
            if (e.keyCode === 27) {
                // enable scrolling
                document.body.style.overflow = "auto"
                setLargeView(false)
            }
        }

        document.addEventListener('keydown', handleEscape)

        return () => {
            document.removeEventListener('keydown', handleEscape)
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
                            onClick={(e) => {
                                // return if the click was on the image
                                if (e.target === larrgeViewFileRef.current) {
                                    return
                                }
                                // enable scrolling
                                document.body.style.overflow = "auto"
                                setLargeView(false)
                            }
                            }
                        >
                            {
                                largeViewIsVideo ?
                                    <img src={largeViewFile} alt="large view"
                                        ref={larrgeViewFileRef}
                                    />
                                    :
                                    <iframe src={`https://plyr.link/p/player.html#${convertToBase64(largeViewFile)}`} alt="large view"
                                        style={{ width: "100%", height: "100%" }}
                                        ref={larrgeViewFileRef}
                                        className="plyr"
                                        allowFullScreen
                                        allowtransparency
                                        allow="autoplay"
                                    />
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
                                // if its not a video or image, download it
                                if (!supportedImageTypes.includes("." + file["name"].split('.').pop()) && !supportedVideoTypes.includes("." + file["name"].split('.').pop())) {
                                    downloadFile(file["id"], file["name"])
                                    return
                                }

                                // scroll to top
                                window.scrollTo(0, 0)
                                // disable scrolling
                                document.body.style.overflow = "hidden"
                                setLargeView(true)
                                setLargeViewFile(`${API_URL}/view/${file["id"]}`)
                                let video = supportedVideoTypes.includes("." + `${API_URL}/view/${file["id"]}`.split('.').pop());
                                setLargeViewIsVideo(video)
                            }}>
                                {/* if the file is a video, add a play button */}
                                {supportedVideoTypes.includes("." + file["name"].split('.').pop()) ? <img src={PlayIcon} alt="play" /> : null}
                                <img src={`${API_URL}/view/${file["id"]}?preview=true`} alt={file} />
                            </div>
                            <div className="controls">
                                <p>{file["name"].length > 15 ? file["name"].substring(0, 15) + "..." : file["name"]}</p>
                                <Button>
                                    <img src={DownloadIcon} alt="Download" onClick={() => downloadFile(file["id"], file["name"])} />
                                </Button>
                                <Button>
                                    <img src={DeleteIcon} alt="Delete" onClick={() => deleteFile(file["id"])} />
                                </Button>
                                <Button
                                    onClick={() => {
                                        console.log(supportedVideoTypes)
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
            <div className="footer">
                Storage Information: Total {bytesToGB(storageinfo["total"])} GB, Used {bytesToGB(storageinfo["used"])} GB, Free {bytesToGB(storageinfo["free"])} GB
            </div>
        </>)
}


export default App
