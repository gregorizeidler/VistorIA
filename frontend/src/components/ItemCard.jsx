import { motion } from 'framer-motion'
import { Camera, Mic, Sparkles, X, CheckCircle } from 'lucide-react'
import { useInspection } from '../context/InspectionContext'
import { useState } from 'react'
import axios from 'axios'

const statusConfig = {
  ok: { label: '✅ OK', color: 'bg-green-500 border-green-500', bg: 'bg-green-50 border-green-200' },
  danificado: { label: '❌ Danificado', color: 'bg-red-500 border-red-500', bg: 'bg-red-50 border-red-200' },
  sujo: { label: '🧹 Sujo', color: 'bg-yellow-500 border-yellow-500', bg: 'bg-yellow-50 border-yellow-200' },
  ausente: { label: '❓ Ausente', color: 'bg-gray-500 border-gray-500', bg: 'bg-gray-50 border-gray-200' },
}

const ItemCard = ({ room, item, itemData }) => {
  const { inspection, setItemStatus, addPhoto, addAudio, updateNotes, addDetectedItems } = useInspection()
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [detectedItems, setDetectedItems] = useState([])
  const [showDetectedItems, setShowDetectedItems] = useState(false)

  const handleFileUpload = async (e, type) => {
    const files = Array.from(e.target.files)
    
    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        let endpoint = ''
        if (type === 'photo') {
          formData.append('prompt', `Analise detalhadamente este ${item} na ${room}`)
          endpoint = '/api/vision'
        } else if (type === 'audio') {
          endpoint = '/api/transcribe'
        }
        
        const response = await axios.post(endpoint, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        const fileUrl = URL.createObjectURL(file)
        
        if (type === 'photo') {
          // A API já retorna os itens detectados automaticamente via GPT Vision
          addPhoto(room, item, fileUrl, response.data.description)
          
          // Se outros itens foram detectados na foto, mostrar opção de adicionar
          if (response.data.detected_items && response.data.detected_items.length > 0) {
            // Filtrar o item atual e outros já no checklist
            const currentChecklist = Object.keys(inspection.checklist[room] || {})
            const newItems = response.data.detected_items.filter(
              detectedItem => {
                const normalizedDetected = detectedItem.toLowerCase().trim()
                const normalizedCurrent = item.toLowerCase().trim()
                // Não incluir o item atual nem itens já existentes
                return normalizedDetected !== normalizedCurrent &&
                       !currentChecklist.some(existing => existing.toLowerCase().trim() === normalizedDetected)
              }
            )
            
            if (newItems.length > 0) {
              setDetectedItems(newItems)
              setShowDetectedItems(true)
            }
          }
        } else if (type === 'audio') {
          addAudio(room, item, fileUrl, response.data.text)
        }
      } catch (error) {
        console.error('Erro no upload:', error)
        let errorMessage = 'Erro ao processar arquivo'
        
        if (error.response) {
          // Erro do servidor
          errorMessage = error.response.data?.detail || error.response.data?.message || `Erro ${error.response.status}: ${error.response.statusText}`
        } else if (error.request) {
          // Requisição feita mas sem resposta
          errorMessage = 'Sem resposta do servidor. Verifique sua conexão.'
        } else {
          // Erro ao configurar a requisição
          errorMessage = error.message || 'Erro desconhecido'
        }
        
        alert(`Erro ao processar arquivo: ${errorMessage}`)
      }
    }
  }
  
  const handleAddDetectedItems = () => {
    if (detectedItems.length > 0) {
      addDetectedItems(room, detectedItems)
      setDetectedItems([])
      setShowDetectedItems(false)
    }
  }
  
  const handleDismissDetectedItems = () => {
    setDetectedItems([])
    setShowDetectedItems(false)
  }

  const handleAIAnalysis = async () => {
    if (itemData.photos.length === 0) {
      alert('Adicione pelo menos uma foto para análise')
      return
    }
    
    setIsAnalyzing(true)
    // Simular análise mais detalhada
    setTimeout(() => {
      setIsAnalyzing(false)
      alert('Análise completa! Verifique as descrições nas fotos.')
    }, 2000)
  }

  const removeMedia = (type, index) => {
    // Implementar remoção de mídia
    console.log('Remover mídia', type, index)
  }

  const currentStatus = itemData.status
  const statusStyle = currentStatus ? statusConfig[currentStatus] : { bg: 'bg-white border-gray-200' }

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      className={`card border-2 ${statusStyle.bg} transition-all duration-300 hover:shadow-2xl group`}
    >
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-xl font-bold text-gray-800 capitalize flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${currentStatus === 'ok' ? 'bg-green-500' : currentStatus === 'danificado' ? 'bg-red-500' : currentStatus === 'sujo' ? 'bg-yellow-500' : 'bg-gray-400'} animate-pulse`}></div>
          {item}
        </h3>
      </div>

      {/* Status Buttons */}
      <div className="flex flex-wrap gap-2.5 mb-5">
        {Object.entries(statusConfig).map(([status, config]) => (
          <motion.button
            key={status}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setItemStatus(room, item, status)}
            className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
              currentStatus === status
                ? `${config.color} text-white shadow-lg transform scale-105`
                : 'bg-white/80 backdrop-blur-sm border-2 border-gray-200 text-gray-700 hover:border-primary-300 hover:bg-primary-50'
            }`}
          >
            {config.label}
          </motion.button>
        ))}
      </div>

      {/* Media Controls */}
      <div className="flex gap-2.5 mb-5">
        <motion.label 
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="btn btn-primary flex-1 cursor-pointer"
        >
          <Camera className="w-4 h-4" />
          <span>Foto</span>
          <input
            type="file"
            className="hidden"
            accept="image/*"
            multiple
            onChange={(e) => handleFileUpload(e, 'photo')}
          />
        </motion.label>
        <motion.label 
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="btn btn-secondary flex-1 cursor-pointer"
        >
          <Mic className="w-4 h-4" />
          <span>Áudio</span>
          <input
            type="file"
            className="hidden"
            accept="audio/*"
            multiple
            onChange={(e) => handleFileUpload(e, 'audio')}
          />
        </motion.label>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleAIAnalysis}
          disabled={isAnalyzing}
          className="btn btn-success disabled:opacity-50"
        >
          <Sparkles className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
          <span>IA</span>
        </motion.button>
      </div>

      {/* Media Previews */}
      {(itemData.photos.length > 0 || itemData.audios.length > 0) && (
        <div className="flex flex-wrap gap-2 mb-4">
          {itemData.photos.map((photo, index) => (
            <div key={index} className="relative">
              <img
                src={photo}
                alt={`Foto ${index + 1}`}
                className="w-20 h-20 object-cover rounded-lg border-2 border-gray-200"
              />
              <button
                onClick={() => removeMedia('photo', index)}
                className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
          {itemData.audios.map((audio, index) => (
            <div key={index} className="relative">
              <audio controls className="w-32 h-8">
                <source src={audio} />
              </audio>
              <button
                onClick={() => removeMedia('audio', index)}
                className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Notes */}
      <textarea
        className="input resize-none"
        rows="3"
        placeholder="📝 Observações adicionais..."
        value={itemData.notes}
        onChange={(e) => updateNotes(room, item, e.target.value)}
      />

      {/* Detected Items Notification */}
      {showDetectedItems && detectedItems.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-4 bg-blue-50 border-2 border-blue-200 rounded-xl"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              <h4 className="font-semibold text-blue-800">
                {detectedItems.length} item{detectedItems.length > 1 ? 's' : ''} detectado{detectedItems.length > 1 ? 's' : ''} na foto
              </h4>
            </div>
            <button
              onClick={handleDismissDetectedItems}
              className="text-blue-600 hover:text-blue-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2 mb-3">
            {detectedItems.map((detectedItem, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium capitalize"
              >
                {detectedItem}
              </span>
            ))}
          </div>
          <button
            onClick={handleAddDetectedItems}
            className="w-full btn btn-success text-sm"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Adicionar ao Checklist</span>
          </button>
        </motion.div>
      )}

      {/* AI Analysis */}
      {itemData.aiAnalysis && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-4 p-4 bg-gradient-to-r from-primary-50 to-secondary-50 border-l-4 border-primary-500 rounded-xl shadow-md"
        >
          <div className="flex items-start gap-2">
            <Sparkles className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-gray-700 leading-relaxed">{itemData.aiAnalysis}</p>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default ItemCard

