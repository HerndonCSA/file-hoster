import {useEffect, useState} from 'react'

const API_URL = 'https://7a7b-2a09-bac1-7681-62b0-00-10-46b.ngrok.io'


function App() {
    const [files, setFiles] = useState([])

    useEffect(() => {
        fetch(`${API_URL}/files`)
            .then(response => response.json())
            .then(data => {
                console.log(data['files'])
                setFiles(data['files'])
            })
    }, [])

    return (<div className="app"
                 onDrop={e => {
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

                 }}
                 onDragOver={e => e.preventDefault()}
                 onDragEnter={e => e.preventDefault()}
                 onDragLeave={e => e.preventDefault()}
                 onDragEnd={e => e.preventDefault()}
                 onDragExit={e => e.preventDefault()}
                 onDragStart={e => e.preventDefault()}
                 onDrag={e => e.preventDefault()}


    >
        <div className="flex">
            <h1>Drag an image to upload</h1>
            <button
                onClick={() => {
                    // upload images from clients file system
                    const input = document.createElement('input')
                    // only allow images
                    input.setAttribute('type', 'file')
                    input.setAttribute('accept', 'image/*')

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
                }}
            > or press to upload
            </button>
        </div>
        <div className="images">
            {files.map(file => {
                if (2 ) return (<div key={file}>
                        <div className="image">
                            <img src={`${API_URL}/view/${file}`} alt={file}/>
                            <div className="action-bar">
                                <h1>{file}</h1>
                                <button
                                    onClick={() => {
                                        fetch(`${API_URL}/delete/${file}`, {
                                            method: 'DELETE'
                                        })
                                            .then(response => response.json())
                                            .then(data => {
                                                console.log(data)
                                                setFiles(data['files'])
                                            })
                                    }}
                                >Delete
                                </button>
                                <button
                                    onClick={() => {
                                        // copy image url to clipboard
                                        navigator.clipboard.writeText(`${API_URL}/view/${file}?embed=true`).then(() => {
                                            alert('Copied to clipboard')
                                        }
                                        )
                                    }}
                                >Embed
                                </button>
                            </div>
                        </div>
                    <img src={`${API_URL}/view/${file}`} alt={file}/>
                </div>)
            })}
        </div>
    </div>)
}


export default App
