import React, { useState, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';
import ApiService from '../services/ApiService';

const DocumentUpload = ({ onUploadSuccess, debugMode = false }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [textContent, setTextContent] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);

  // Handle file drag and drop
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    // Validate file type
    if (!file.type.startsWith('text/') && 
        !['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
      toast.error('Please upload a text file, PDF, or Word document');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      if (debugMode) {
        console.log('🔍 DEBUG: Starting file upload', {
          filename: file.name,
          size: `${(file.size / 1024).toFixed(2)} KB`,
          type: file.type,
          timestamp: new Date().toISOString()
        });
      }

      const result = await ApiService.uploadFile(file, (progress) => {
        setUploadProgress(progress);
        if (debugMode) {
          console.log(`🔍 DEBUG: Upload progress: ${progress}%`);
        }
      });

      if (debugMode) {
        console.log('🔍 DEBUG: File upload response', result);
      }

      toast.success(`File uploaded successfully! Processing started.`);
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }

    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.message || 'Failed to upload file');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleTextUpload = async () => {
    if (!textContent.trim()) {
      toast.error('Please enter some content');
      return;
    }

    if (textContent.length < 100) {
      toast.error('Content must be at least 100 characters long');
      return;
    }

    setUploading(true);

    try {
      if (debugMode) {
        console.log('🔍 DEBUG: Starting text upload', {
          contentLength: textContent.length,
          timestamp: new Date().toISOString()
        });
      }

      const result = await ApiService.uploadText(textContent);

      if (debugMode) {
        console.log('🔍 DEBUG: Text upload response', result);
      }

      toast.success('Content uploaded successfully! Processing started.');
      setTextContent('');
      setShowTextInput(false);
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }

    } catch (error) {
      console.error('Text upload error:', error);
      toast.error(error.response?.data?.message || 'Failed to upload content');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Toggle buttons */}
      <div className="flex justify-center mb-6">
        <div className="bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setShowTextInput(false)}
            className={`px-4 py-2 rounded-md transition-all ${
              !showTextInput 
                ? 'bg-primary-500 text-white shadow-md' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Upload File
          </button>
          <button
            onClick={() => setShowTextInput(true)}
            className={`px-4 py-2 rounded-md transition-all ${
              showTextInput 
                ? 'bg-primary-500 text-white shadow-md' 
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Paste Content
          </button>
        </div>
      </div>

      {!showTextInput ? (
        /* File Upload UI */
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
            dragActive
              ? 'border-primary-400 bg-primary-50'
              : uploading
              ? 'border-success-400 bg-success-50'
              : 'border-gray-300 hover:border-primary-300 hover:bg-gray-50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {uploading ? (
            <div className="space-y-4">
              <div className="animate-spin-slow">
                <Upload className="w-12 h-12 text-success-500 mx-auto" />
              </div>
              <div>
                <p className="text-lg font-medium text-success-700">
                  Uploading... {uploadProgress}%
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-success-500 h-2 rounded-full progress-bar"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className={`transition-all ${dragActive ? 'scale-110' : ''}`}>
                <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              </div>
              <div>
                <p className="text-lg font-medium text-gray-700">
                  {dragActive ? 'Drop your file here' : 'Upload your BRD or User Stories'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Drag and drop or click to browse • Max 10MB
                </p>
              </div>
              <input
                type="file"
                onChange={handleFileChange}
                accept=".txt,.doc,.docx,.pdf"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={uploading}
              />
            </div>
          )}
        </div>
      ) : (
        /* Text Input UI */
        <div className="space-y-4">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-primary-500" />
                <h3 className="font-medium text-gray-900">Paste Your Content</h3>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Paste your BRD, User Stories, or Requirements (minimum 100 characters)
              </p>
            </div>
            <div className="p-4">
              <textarea
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="Paste your BRD or User Stories content here..."
                className="w-full h-64 p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent custom-scrollbar"
                disabled={uploading}
              />
              <div className="flex justify-between items-center mt-3">
                <div className="text-sm text-gray-500">
                  {textContent.length} characters
                  {textContent.length < 100 && (
                    <span className="text-warning-600 ml-1">
                      (minimum 100 required)
                    </span>
                  )}
                </div>
                <button
                  onClick={handleTextUpload}
                  disabled={uploading || textContent.length < 100}
                  className="px-6 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {uploading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Processing...</span>
                    </div>
                  ) : (
                    'Upload Content'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File format info */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-blue-900 mb-1">Supported Formats</p>
            <ul className="text-blue-700 space-y-1">
              <li>• Text files (.txt)</li>
              <li>• Word documents (.doc, .docx)</li>
              <li>• PDF documents (.pdf)</li>
              <li>• Plain text content (pasted directly)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Processing info */}
      <div className="mt-4 p-4 bg-green-50 rounded-lg">
        <div className="flex items-start space-x-3">
          <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-green-900 mb-1">What Happens Next?</p>
            <ol className="text-green-700 space-y-1 list-decimal list-inside">
              <li>Document is analyzed and chunked into semantic segments</li>
              <li>AI generates embeddings for each chunk</li>
              <li>Chunks are clustered by functionality</li>
              <li>Gemini 2.0 generates tailored test recommendations</li>
              <li>Results are displayed in an organized dashboard</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;