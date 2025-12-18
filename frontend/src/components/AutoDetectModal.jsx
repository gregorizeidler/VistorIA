import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Upload, Sparkles, CheckCircle, Loader } from 'lucide-react'
import { useInspection } from '../context/InspectionContext'
import axios from 'axios'

const AutoDetectModal = ({ isOpen, onClose, roomName }) => {
  const { addDetectedItems } = useInspection()
  const [files, setFiles] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [detectedItems, setDetectedItems] = useState([])
  const [error, setError] = useState(null)

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files)
    setFiles(prev => [...prev, ...selectedFiles])
    setError(null)
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleDetect = async () => {
    if (files.length === 0) {
      setError('Por favor, selecione pelo menos uma foto')
      return
    }

    setIsProcessing(true)
    setError(null)
    setDetectedItems([])

    try {
      const formData = new FormData()
      files.forEach(file => {
        formData.append('files', file)
      })

      const response = await axios.post('/api/auto-checklist', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.data.detected_items && response.data.detected_items.length > 0) {
        setDetectedItems(response.data.detected_items)
      } else {
        setError('Nenhum item foi detectado nas fotos. Tente com outras imagens.')
      }
    } catch (err) {
      console.error('Erro na detecção:', err)
      let errorMessage = 'Erro ao processar as imagens'
      
      if (err.response) {
        // Erro do servidor
        errorMessage = err.response.data?.detail || err.response.data?.message || `Erro ${err.response.status}: ${err.response.statusText}`
      } else if (err.request) {
        // Requisição feita mas sem resposta
        errorMessage = 'Sem resposta do servidor. Verifique sua conexão e tente novamente.'
      } else {
        // Erro ao configurar a requisição
        errorMessage = err.message || 'Erro desconhecido'
      }
      
      setError(errorMessage)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleAddItems = () => {
    if (detectedItems.length > 0 && roomName) {
      addDetectedItems(roomName, detectedItems)
      handleClose()
    }
  }

  const handleClose = () => {
    setFiles([])
    setDetectedItems([])
    setError(null)
    setIsProcessing(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        onClick={handleClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold gradient-text">Auto-Detecção de Itens</h2>
                <p className="text-sm text-gray-500">Envie fotos do cômodo para detectar itens automaticamente</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="w-10 h-10 rounded-xl hover:bg-gray-100 flex items-center justify-center transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Room Info */}
            {roomName && (
              <div className="mb-6 p-4 bg-primary-50 rounded-xl border border-primary-200">
                <p className="text-sm font-semibold text-primary-700">
                  📍 Cômodo: <span className="capitalize">{roomName}</span>
                </p>
              </div>
            )}

            {/* File Upload */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Selecione fotos do cômodo:
              </label>
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-primary-500 transition-colors bg-gray-50 hover:bg-primary-50">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-10 h-10 text-gray-400 mb-2" />
                  <p className="mb-2 text-sm text-gray-500">
                    <span className="font-semibold">Clique para selecionar</span> ou arraste as fotos
                  </p>
                  <p className="text-xs text-gray-500">PNG, JPG, WEBP (máx. 10MB cada)</p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  accept="image/*"
                  multiple
                  onChange={handleFileSelect}
                />
              </label>

              {/* File List */}
              {files.length > 0 && (
                <div className="mt-4 space-y-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <span className="text-primary-600 font-bold text-xs">IMG</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-700 truncate">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="w-8 h-8 rounded-lg hover:bg-red-100 flex items-center justify-center transition-colors ml-2"
                      >
                        <X className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl"
              >
                <p className="text-sm text-red-700">{error}</p>
              </motion.div>
            )}

            {/* Detected Items */}
            {detectedItems.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4"
              >
                <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  Itens Detectados ({detectedItems.length})
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {detectedItems.map((item, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm font-medium text-gray-700 capitalize">{item}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Processing Indicator */}
            {isProcessing && (
              <div className="flex flex-col items-center justify-center py-8">
                <Loader className="w-12 h-12 text-primary-600 animate-spin mb-4" />
                <p className="text-gray-600 font-medium">Processando imagens com IA...</p>
                <p className="text-sm text-gray-500 mt-2">Isso pode levar alguns segundos</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
            <button
              onClick={handleClose}
              className="px-6 py-3 rounded-xl font-semibold text-gray-700 hover:bg-gray-200 transition-colors"
            >
              Cancelar
            </button>
            <div className="flex gap-3">
              {detectedItems.length === 0 && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleDetect}
                  disabled={files.length === 0 || isProcessing}
                  className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Sparkles className="w-5 h-5" />
                  <span>{isProcessing ? 'Processando...' : 'Detectar Itens'}</span>
                </motion.button>
              )}
              {detectedItems.length > 0 && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleAddItems}
                  className="btn btn-success"
                >
                  <CheckCircle className="w-5 h-5" />
                  <span>Adicionar ao Checklist</span>
                </motion.button>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

export default AutoDetectModal

