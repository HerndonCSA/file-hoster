import {useEffect, useState} from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'


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

    return (<div className="App"
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
        </div>
        <div className="images">
            {files.map(file => (<div key={file}>
                <img src={`${API_URL}/view/${file}`} alt={file}/>
            </div>))}
        </div>
    </div>)
}


export default App
