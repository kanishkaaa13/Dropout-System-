import { useState } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react'
import Papa from 'papaparse'

export default function CSVBulkUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null) // 'success' | 'error' | null
  const [errorMessage, setErrorMessage] = useState('')
  const [previewData, setPreviewData] = useState([])

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files[0]
    if (selectedFile && selectedFile.type === 'text/csv' || selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile)
      setUploadStatus(null)
      setErrorMessage('')
      
      // Parse CSV for preview
      Papa.parse(selectedFile, {
        header: true,
        preview: 5,
        complete: (results) => {
          setPreviewData(results.data)
        },
        error: (error) => {
          setErrorMessage('Failed to parse CSV file')
          setUploadStatus('error')
        }
      })
    } else {
      setErrorMessage('Please select a valid CSV file')
      setUploadStatus('error')
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setUploadStatus(null)

    try {
      // Parse the entire CSV file
      Papa.parse(file, {
        header: true,
        complete: async (results) => {
          try {
            const response = await fetch('/api/v1/students/bulk-upload', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                students: results.data
              })
            })

            if (response.ok) {
              const data = await response.json()
              setUploadStatus('success')
              onUploadSuccess?.(data)
              setFile(null)
              setPreviewData([])
            } else {
              const error = await response.json()
              setErrorMessage(error.detail || 'Upload failed')
              setUploadStatus('error')
            }
          } catch (error) {
            setErrorMessage('Upload failed: ' + error.message)
            setUploadStatus('error')
          } finally {
            setUploading(false)
          }
        },
        error: (error) => {
          setErrorMessage('Failed to parse CSV file')
          setUploadStatus('error')
          setUploading(false)
        }
      })
    } catch (error) {
      setErrorMessage('Upload failed: ' + error.message)
      setUploadStatus('error')
      setUploading(false)
    }
  }

  const handleRemoveFile = () => {
    setFile(null)
    setPreviewData([])
    setUploadStatus(null)
    setErrorMessage('')
  }

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      {!file ? (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition cursor-pointer">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            className="hidden"
            id="csv-upload"
          />
          <label htmlFor="csv-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-sm text-gray-600 mb-2">
              Click to upload or drag and drop
            </p>
            <p className="text-xs text-gray-500">
              CSV files only (max 10MB)
            </p>
          </label>
        </div>
      ) : (
        /* File Preview */
        <div className="border border-gray-300 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
              </div>
            </div>
            <button
              onClick={handleRemoveFile}
              className="text-gray-400 hover:text-gray-600 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Data Preview */}
          {previewData.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-700 mb-2">Preview (first 5 rows):</p>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(previewData[0]).map(key => (
                        <th key={key} className="px-3 py-2 text-left font-medium text-gray-700">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {previewData.map((row, index) => (
                      <tr key={index}>
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="px-3 py-2 text-gray-600">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {uploading ? 'Uploading...' : 'Upload CSV'}
          </button>
        </div>
      )}

      {/* Status Messages */}
      {uploadStatus === 'success' && (
        <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <p className="text-sm text-green-800">CSV uploaded successfully!</p>
        </div>
      )}

      {uploadStatus === 'error' && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-sm text-red-800">{errorMessage}</p>
        </div>
      )}

      {/* Instructions */}
      <div className="text-xs text-gray-500 space-y-1">
        <p><strong>CSV Format Requirements:</strong></p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>First row must contain column headers</li>
          <li>Required columns: full_name, email, batch_id</li>
          <li>Optional columns: attendance_rate, mock_test_avg, physics_score, chemistry_score, maths_score</li>
          <li>Maximum file size: 10MB</li>
        </ul>
      </div>
    </div>
  )
}
