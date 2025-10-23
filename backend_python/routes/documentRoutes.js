const express = require('express');
const multer = require('multer');
const router = express.Router();

const { DebugLogger } = require('../services/DebugLogger');
const supabaseService = require('../services/supabaseClient');
const EmbedService = require('../services/EmbedService');
const ClusterService = require('../services/ClusterService');
const GeminiService = require('../services/GeminiService');

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB
  },
  fileFilter: (req, file, cb) => {
    // Accept text files and documents
    const allowedTypes = ['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (file.mimetype.startsWith('text/') || allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Please upload text files only.'));
    }
  }
});

// Upload and process document
router.post('/upload', upload.single('document'), async (req, res) => {
  try {
    DebugLogger.logProgress(1, 8, 'Document upload started');

    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { originalname, mimetype, size, buffer } = req.file;
    const content = buffer.toString('utf-8');

    DebugLogger.logFileUpload(originalname, size, mimetype);

    // Step 1: Insert document record
    const documentData = {
      filename: originalname,
      content: content,
      content_type: mimetype,
      file_size: size,
      processing_status: 'processing'
    };

    const document = await supabaseService.insertDocument(documentData);
    DebugLogger.logProgress(2, 8, 'Document record created');

    // Return document ID immediately for frontend tracking
    res.json({
      success: true,
      documentId: document.id,
      message: 'Document uploaded successfully. Processing started.',
      status: 'processing'
    });

    // Continue processing in background
    processDocumentInBackground(document.id, content, originalname);

  } catch (error) {
    DebugLogger.logError('document_upload', error);
    res.status(500).json({ 
      error: 'Failed to upload document', 
      message: error.message 
    });
  }
});

// Upload text content directly (without file)
router.post('/upload-text', async (req, res) => {
  try {
    const { content, filename = 'pasted-content.txt' } = req.body;

    if (!content || content.trim().length === 0) {
      return res.status(400).json({ error: 'No content provided' });
    }

    DebugLogger.logFileUpload(filename, content.length, 'text/plain');

    // Insert document record
    const documentData = {
      filename: filename,
      content: content,
      content_type: 'text/plain',
      file_size: content.length,
      processing_status: 'processing'
    };

    const document = await supabaseService.insertDocument(documentData);

    res.json({
      success: true,
      documentId: document.id,
      message: 'Content uploaded successfully. Processing started.',
      status: 'processing'
    });

    // Process in background
    processDocumentInBackground(document.id, content, filename);

  } catch (error) {
    DebugLogger.logError('text_upload', error);
    res.status(500).json({ 
      error: 'Failed to upload content', 
      message: error.message 
    });
  }
});

// Get processing status
router.get('/status/:documentId', async (req, res) => {
  try {
    const { documentId } = req.params;

    const { data, error } = await supabaseService.supabase
      .from('documents')
      .select('processing_status, total_chunks, upload_timestamp')
      .eq('id', documentId)
      .single();

    if (error) {
      throw error;
    }

    res.json({
      documentId,
      status: data.processing_status,
      totalChunks: data.total_chunks,
      uploadTimestamp: data.upload_timestamp
    });

  } catch (error) {
    DebugLogger.logError('get_status', error, { documentId: req.params.documentId });
    res.status(500).json({ 
      error: 'Failed to get status', 
      message: error.message 
    });
  }
});

// Get all documents
router.get('/list', async (req, res) => {
  try {
    const { data, error } = await supabaseService.supabase
      .from('documents')
      .select('id, filename, processing_status, total_chunks, upload_timestamp')
      .order('upload_timestamp', { ascending: false });

    if (error) {
      throw error;
    }

    res.json({
      documents: data
    });

  } catch (error) {
    DebugLogger.logError('list_documents', error);
    res.status(500).json({ 
      error: 'Failed to list documents', 
      message: error.message 
    });
  }
});

// Delete document and all related data
router.delete('/:documentId', async (req, res) => {
  try {
    const { documentId } = req.params;

    const success = await supabaseService.deleteDocumentAndRelatedData(documentId);

    if (success) {
      res.json({
        success: true,
        message: 'Document and all related data deleted successfully'
      });
    } else {
      res.status(500).json({
        error: 'Failed to delete document'
      });
    }

  } catch (error) {
    DebugLogger.logError('delete_document', error, { documentId: req.params.documentId });
    res.status(500).json({ 
      error: 'Failed to delete document', 
      message: error.message 
    });
  }
});

// Reprocess document (regenerate recommendations)
router.post('/reprocess/:documentId', async (req, res) => {
  try {
    const { documentId } = req.params;

    // Get document content
    const { data, error } = await supabaseService.supabase
      .from('documents')
      .select('content, filename')
      .eq('id', documentId)
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'Document not found' });
    }

    // Update status to processing
    await supabaseService.updateDocumentStatus(documentId, 'processing');

    res.json({
      success: true,
      message: 'Document reprocessing started',
      documentId
    });

    // Reprocess in background
    processDocumentInBackground(documentId, data.content, data.filename);

  } catch (error) {
    DebugLogger.logError('reprocess_document', error, { documentId: req.params.documentId });
    res.status(500).json({ 
      error: 'Failed to reprocess document', 
      message: error.message 
    });
  }
});

// Background processing function
async function processDocumentInBackground(documentId, content, filename) {
  try {
    DebugLogger.logProgress(3, 8, 'Starting background processing');

    // Step 1: Process document into embeddings
    const processResult = await EmbedService.processDocument(content, filename, documentId);
    DebugLogger.logProgress(4, 8, 'Document processed and chunked');

    // Step 2: Store embeddings in database
    await supabaseService.insertEmbeddings(processResult.embeddings);
    await supabaseService.updateDocumentStatus(documentId, 'embedding_complete', processResult.totalChunks);
    DebugLogger.logProgress(5, 8, 'Embeddings stored in database');

    // Step 3: Perform clustering
    const clusterResult = await ClusterService.clusterEmbeddings(processResult.embeddings);
    DebugLogger.logProgress(6, 8, 'Clustering completed');

    // Step 4: Update cluster assignments
    await supabaseService.updateEmbeddingClusters(documentId, clusterResult.clusterAssignments);

    // Step 5: Generate cluster summaries and test recommendations
    const clusteredChunks = ClusterService.groupChunksByCluster(clusterResult.clusterAssignments);
    
    for (const [clusterId, chunks] of Object.entries(clusteredChunks)) {
      DebugLogger.logProgress(7, 8, `Processing cluster ${clusterId}`);

      // Generate cluster summary
      const chunkTexts = chunks.map(chunk => chunk.text);
      const clusterSummary = await GeminiService.generateClusterSummary(chunkTexts, parseInt(clusterId));

      // Store cluster summary
      await supabaseService.insertClusterSummary({
        document_id: documentId,
        cluster_id: parseInt(clusterId),
        summary: clusterSummary.summary,
        chunk_count: chunks.length,
        feature_category: clusterSummary.featureCategory
      });

      // Generate test recommendations
      const testRecommendations = await GeminiService.generateTestRecommendations(
        clusterSummary.summary,
        chunkTexts
      );

      // Store test recommendations
      await supabaseService.insertTestRecommendations({
        document_id: documentId,
        cluster_id: parseInt(clusterId),
        cluster_summary: clusterSummary.summary,
        standard_tests: testRecommendations.standardTests,
        recommended_tests: testRecommendations.recommendedTests,
        test_metadata: {
          testCategories: testRecommendations.testCategories,
          clusterInfo: clusterSummary,
          chunkCount: chunks.length
        }
      });
    }

    // Step 6: Update final status
    await supabaseService.updateDocumentStatus(documentId, 'completed');
    DebugLogger.logProgress(8, 8, 'Document processing completed successfully');

  } catch (error) {
    DebugLogger.logError('background_processing', error, { documentId, filename });
    
    // Update status to failed
    try {
      await supabaseService.updateDocumentStatus(documentId, 'failed');
    } catch (statusError) {
      DebugLogger.logError('update_failed_status', statusError, { documentId });
    }
  }
}

module.exports = router;