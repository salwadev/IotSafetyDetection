import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts'

function App() {
  const [mode, setMode] = useState(null) // null, 'image' ou 'video'
  const [detections, setDetections] = useState([])
  const [isSecure, setIsSecure] = useState(true)
  const [imagePreview, setImagePreview] = useState(null)
  const [videoStream, setVideoStream] = useState(null)
  const [history, setHistory] = useState([])
  const [isAlertPlaying, setIsAlertPlaying] = useState(false)
  const videoRef = useRef(null)
  const fileInputRef = useRef(null)
  
  const alertAudio = new Audio('/alert.mp3')
  const [alarmAudio] = useState(new Audio('/alert.wav'))
  
  useEffect(() => {
    if (!isSecure && !isAlertPlaying) {
      alertAudio.play()
      setIsAlertPlaying(true)
    } else if (isSecure && isAlertPlaying) {
      alertAudio.pause()
      alertAudio.currentTime = 0
      setIsAlertPlaying(false)
    }
  }, [isSecure])

  useEffect(() => {
    if (!isSecure) {
        alarmAudio.loop = true
        alarmAudio.play()
    } else {
        alarmAudio.pause()
        alarmAudio.currentTime = 0
    }
    
    return () => {
        alarmAudio.pause()
        alarmAudio.currentTime = 0
    }
  }, [isSecure])

  useEffect(() => {
    let ws = null;
    
    if (mode === 'video') {
      // Créer une connexion WebSocket
      ws = new WebSocket('ws://localhost:5000/ws');
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setDetections(data.detections);
        setIsSecure(data.is_secure);
        
        // Mettre à jour les statistiques
        setStatistics({
          total_persons: data.total_persons,
          secured_persons: data.secured_persons,
          partially_secured: data.partially_secured,
          unsecured: data.unsecured
        });
      };
      
      // Charger l'historique périodiquement
      const historyInterval = setInterval(loadHistory, 5000);
      
      return () => {
        if (ws) ws.close();
        clearInterval(historyInterval);
      };
    }
  }, [mode]);

  const [statistics, setStatistics] = useState({
    total_persons: 0,
    secured_persons: 0,
    partially_secured: 0,
    unsecured: 0
  });

  const handleImageClick = () => {
    fileInputRef.current.click();
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    setMode('image')
    const formData = new FormData()
    formData.append('image', file)
    
    try {
      const response = await axios.post('http://localhost:5000/detect', formData)
      setDetections(response.data.detections)
      setIsSecure(response.data.is_secure)
      
      setImagePreview(`data:image/jpeg;base64,${response.data.image}`)
    } catch (error) {
      console.error('Error detecting objects:', error)
    }
  }

  const toggleVideoDetection = async () => {
    if (mode === 'video') {
        try {
            // Arrêter la vidéo côté serveur
            await axios.get('http://localhost:5000/stop-video')
            setMode(null)
            setVideoStream(null)
            setDetections([])
            setIsSecure(true)
            setStatistics({
                total_persons: 0,
                secured_persons: 0,
                partially_secured: 0,
                unsecured: 0
            })
            // Forcer le rafraîchissement de l'image
            const timestamp = new Date().getTime()
            setVideoStream(`http://localhost:5000/video-feed?t=${timestamp}`)
        } catch (error) {
            console.error('Erreur lors de l\'arrêt de la caméra:', error)
        }
    } else {
        try {
            setMode('video')
            // Ajouter un timestamp pour éviter la mise en cache
            const timestamp = new Date().getTime()
            setVideoStream(`http://localhost:5000/video-feed?t=${timestamp}`)
        } catch (error) {
            console.error('Erreur lors de l\'accès à la caméra:', error)
            alert('Impossible d\'accéder à la caméra')
        }
    }
  }

  const formatHistoryData = (data) => {
    return data.map(entry => {
      const formattedTimestamp = new Date(entry.timestamp);
      return {
        ...entry,
        timestamp: formattedTimestamp.toString() !== "Invalid Date" ? formattedTimestamp.toLocaleString() : "Date invalide", // Vérification de la validité
        confidence: parseFloat(entry.confidence)
      };
    });
  }

  const loadHistory = async () => {
    try {
      const response = await axios.get('http://localhost:5000/get-history');
      console.log(response.data); // Vérifiez les données ici
      setHistory(formatHistoryData(response.data));
    } catch (error) {
      console.error('Error loading history:', error)
    }
  }

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const paginatedHistory = history.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const totalPages = Math.ceil(history.length / itemsPerPage);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Détection d'EPI en temps réel</h1>
        <div className="detection-controls">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            style={{ display: 'none' }}
          />
          <button 
            className={`control-button ${mode === 'image' ? 'active' : ''}`}
            onClick={handleImageClick}
          >
            <i className="fas fa-image"></i>
            Détecter par Image
          </button>
          <button 
            className={`control-button ${mode === 'video' ? 'active' : ''}`}
            onClick={toggleVideoDetection}
          >
            <i className={`fas ${mode === 'video' ? 'fa-video-slash' : 'fa-video'}`}></i>
            {mode === 'video' ? 'Arrêter la Caméra' : 'Détecter par Caméra'}
          </button>
        </div>
      </header>
      {!isSecure && (
          <div className="alert danger">
            <i className="fas fa-exclamation-triangle"></i>
            ATTENTION: Personne non sécurisée détectée!
          </div>
        )}
      <main className="main-content">
        <div className="detection-display">
          {mode === 'image' && imagePreview && (
            <img src={imagePreview} alt="Preview" className="preview-image" />
          )}
          {mode === 'video' && (
            <>
            <div className="video-container width-60">
              <img 
                src={videoStream} 
                alt="Video Stream" 
                className={`detection-overlay ${isSecure ? 'secure' : 'unsafe'}`}
                style={{ 
                  width: '640px', 
                  height: '480px',
                  display: 'block',
                  objectFit: 'contain'
                }}
              />
            </div>

<div className="current-detections">
<h2>Détections en cours</h2>
<ul className="detections-list">
  {detections.map((detection, index) => (
    <li key={index} className={`detection-item ${
      detection.label === "Non Securisee" ? "unsafe" : 
      detection.label === "Securisee" ? "safe" : ""
    }`}>
      <span className="detection-label">{detection.label}</span>
      <span className="detection-confidence">
        {(detection.confidence * 100).toFixed(2)}%
      </span>
    </li>
  ))}
</ul>
</div>
            </>
          )}
        </div>

        <div className="width-100">
         

          <div className="history-section width-100">
            <div className="history-header">
              <h2>Historique des Détections</h2>
              <button onClick={loadHistory} className="refresh-button">
                <i className="fas fa-sync-alt"></i>
                Actualiser
              </button>
            </div>
            <div className="display-flex">
            <div className="chart-container width-50">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp"
                    angle={-45}
                    textAnchor="end"
                    height={70}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="securise"
                    name="Personnes Sécurisées"
                    stroke="#20bf6b"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="non_securise"
                    name="Personnes Non Sécurisées"
                    stroke="#eb3b5a"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="width-50">
            <div className="table-container">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Date/Heure</th>
                    <th>Total Personnes</th>
                    <th>Sécurisées</th>
                    <th>Non Sécurisées</th>
                    <th>Image</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedHistory.map((entry, index) => (
                    <tr key={index}>
                      <td>{entry.timestamp}</td>
                      <td>{entry.total_persons}</td>
                      <td className="secure-cell">{entry.securise}</td>
                      <td className="unsafe-cell">{entry.non_securise}</td>
                      <td>
                        {entry.image_path && (
                          <img 
                            src={`http://localhost:5000/detections/${entry.image_path}`} 
                            alt="Détection" 
                            className="history-thumbnail"
                            onClick={() => window.open(`http://localhost:5000/detections/${entry.image_path}`, '_blank')}
                          />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          
            {/* Pagination Controls */}
            <div className="pagination-controls">
              {Array.from({ length: totalPages }, (_, index) => (
                <button 
                  key={index} 
                  onClick={() => handlePageChange(index + 1)} 
                  className={`pagination-button ${currentPage === index + 1 ? 'active' : ''}`}
                >
                  {index + 1}
                </button>
              ))}
            </div>
            </div>
            </div>
          </div>
        </div>

        <div className="statistics-panel">
          <h2>Statistiques actuelles</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Total Personnes</span>
              <span className="stat-value">{statistics.total_persons}</span>
            </div>
            <div className="stat-item secure">
              <span className="stat-label">Personnes Sécurisées</span>
              <span className="stat-value">{statistics.secured_persons}</span>
            </div>
            <div className="stat-item partial">
              <span className="stat-label">Partiellement Sécurisées</span>
              <span className="stat-value">{statistics.partially_secured}</span>
            </div>
            <div className="stat-item unsafe">
              <span className="stat-label">Non Sécurisées</span>
              <span className="stat-value">{statistics.unsecured}</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
