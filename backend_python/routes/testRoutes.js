const express = require('express');
const router = express.Router();

const { DebugLogger } = require('../services/DebugLogger');
const supabaseService = require('../services/supabaseClient');
const GeminiService = require('../services/GeminiService');

// Get test recommendations for a document
router.get('/recommendations/:documentId', async (req, res) => {
  try {
    const { documentId } = req.params;

    DebugLogger.logProgress(1, 2, `Fetching test recommendations for document ${documentId}`);

    const testRecommendations = await supabaseService.getTestRecommendationsByDocument(documentId);

    if (!testRecommendations || testRecommendations.length === 0) {
      return res.status(404).json({
        error: 'No test recommendations found',
        message: 'Document may still be processing or no recommendations were generated'
      });
    }

    // Aggregate and format the recommendations
    const formattedRecommendations = formatTestRecommendations(testRecommendations);

    DebugLogger.logProgress(2, 2, 'Test recommendations retrieved successfully');

    res.json({
      documentId,
      recommendations: formattedRecommendations,
      totalClusters: testRecommendations.length,
      aggregatedStats: calculateAggregatedStats(testRecommendations)
    });

  } catch (error) {
    DebugLogger.logError('get_test_recommendations', error, { 
      documentId: req.params.documentId 
    });
    res.status(500).json({ 
      error: 'Failed to get test recommendations', 
      message: error.message 
    });
  }
});

// Regenerate test recommendations for a specific cluster
router.post('/regenerate/:documentId/:clusterId', async (req, res) => {
  try {
    const { documentId, clusterId } = req.params;

    DebugLogger.logProgress(1, 3, `Regenerating tests for cluster ${clusterId}`);

    // Get cluster chunks
    const { data: embeddings, error } = await supabaseService.supabase
      .from('embeddings')
      .select('chunk_text')
      .eq('document_id', documentId)
      .eq('cluster_id', parseInt(clusterId));

    if (error || !embeddings || embeddings.length === 0) {
      return res.status(404).json({
        error: 'Cluster not found or no chunks available'
      });
    }

    const chunkTexts = embeddings.map(e => e.chunk_text);

    // Get existing cluster summary or generate new one
    const { data: existingSummary } = await supabaseService.supabase
      .from('cluster_summaries')
      .select('summary')
      .eq('document_id', documentId)
      .eq('cluster_id', parseInt(clusterId))
      .single();

    let clusterSummary = existingSummary?.summary;
    
    if (!clusterSummary) {
      DebugLogger.logProgress(2, 3, 'Generating new cluster summary');
      const summaryResult = await GeminiService.generateClusterSummary(chunkTexts, parseInt(clusterId));
      clusterSummary = summaryResult.summary;
    }

    // Generate new test recommendations
    DebugLogger.logProgress(3, 3, 'Generating new test recommendations');
    const testRecommendations = await GeminiService.generateTestRecommendations(
      clusterSummary,
      chunkTexts
    );

    // Update database with new recommendations
    await supabaseService.insertTestRecommendations({
      document_id: documentId,
      cluster_id: parseInt(clusterId),
      cluster_summary: clusterSummary,
      standard_tests: testRecommendations.standardTests,
      recommended_tests: testRecommendations.recommendedTests,
      test_metadata: {
        testCategories: testRecommendations.testCategories,
        regeneratedAt: new Date().toISOString(),
        chunkCount: chunkTexts.length
      }
    });

    res.json({
      success: true,
      clusterId: parseInt(clusterId),
      recommendations: {
        standardTests: testRecommendations.standardTests,
        recommendedTests: testRecommendations.recommendedTests,
        testCategories: testRecommendations.testCategories
      },
      clusterSummary
    });

  } catch (error) {
    DebugLogger.logError('regenerate_cluster_tests', error, { 
      documentId: req.params.documentId,
      clusterId: req.params.clusterId 
    });
    res.status(500).json({ 
      error: 'Failed to regenerate test recommendations', 
      message: error.message 
    });
  }
});

// Get aggregated test recommendations across all clusters
router.get('/aggregated/:documentId', async (req, res) => {
  try {
    const { documentId } = req.params;

    const testRecommendations = await supabaseService.getTestRecommendationsByDocument(documentId);

    if (!testRecommendations || testRecommendations.length === 0) {
      return res.status(404).json({
        error: 'No test recommendations found'
      });
    }

    // Aggregate and deduplicate tests
    const aggregatedTests = aggregateAndDeduplicateTests(testRecommendations);

    res.json({
      documentId,
      aggregatedTests,
      sourceClusterCount: testRecommendations.length
    });

  } catch (error) {
    DebugLogger.logError('get_aggregated_tests', error, { 
      documentId: req.params.documentId 
    });
    res.status(500).json({ 
      error: 'Failed to get aggregated tests', 
      message: error.message 
    });
  }
});

// Get test recommendations by category
router.get('/by-category/:documentId', async (req, res) => {
  try {
    const { documentId } = req.params;

    const testRecommendations = await supabaseService.getTestRecommendationsByDocument(documentId);

    if (!testRecommendations || testRecommendations.length === 0) {
      return res.status(404).json({
        error: 'No test recommendations found'
      });
    }

    // Organize tests by category
    const testsByCategory = organizeTestsByCategory(testRecommendations);

    res.json({
      documentId,
      testsByCategory,
      availableCategories: Object.keys(testsByCategory)
    });

  } catch (error) {
    DebugLogger.logError('get_tests_by_category', error, { 
      documentId: req.params.documentId 
    });
    res.status(500).json({ 
      error: 'Failed to get tests by category', 
      message: error.message 
    });
  }
});

// Export test recommendations in various formats
router.get('/export/:documentId/:format', async (req, res) => {
  try {
    const { documentId, format } = req.params;

    const testRecommendations = await supabaseService.getTestRecommendationsByDocument(documentId);

    if (!testRecommendations || testRecommendations.length === 0) {
      return res.status(404).json({
        error: 'No test recommendations found'
      });
    }

    let exportData;
    let contentType = 'application/json';
    let filename = `test_recommendations_${documentId}`;

    switch (format.toLowerCase()) {
      case 'json':
        exportData = JSON.stringify(formatTestRecommendations(testRecommendations), null, 2);
        filename += '.json';
        break;
      
      case 'csv':
        exportData = convertToCSV(testRecommendations);
        contentType = 'text/csv';
        filename += '.csv';
        break;
      
      case 'markdown':
        exportData = convertToMarkdown(testRecommendations);
        contentType = 'text/markdown';
        filename += '.md';
        break;
      
      default:
        return res.status(400).json({
          error: 'Unsupported export format',
          supportedFormats: ['json', 'csv', 'markdown']
        });
    }

    res.setHeader('Content-Type', contentType);
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.send(exportData);

  } catch (error) {
    DebugLogger.logError('export_tests', error, { 
      documentId: req.params.documentId,
      format: req.params.format 
    });
    res.status(500).json({ 
      error: 'Failed to export tests', 
      message: error.message 
    });
  }
});

// Helper functions

function formatTestRecommendations(testRecommendations) {
  return testRecommendations.map(test => ({
    clusterId: test.cluster_id,
    clusterSummary: test.cluster_summary,
    featureCategory: test.cluster_summaries?.[0]?.feature_category || 'General',
    chunkCount: test.cluster_summaries?.[0]?.chunk_count || 0,
    standardTests: test.standard_tests || [],
    recommendedTests: test.recommended_tests || [],
    testCategories: test.test_metadata?.testCategories || {},
    lastUpdated: test.updated_at
  }));
}

function calculateAggregatedStats(testRecommendations) {
  const stats = {
    totalStandardTests: 0,
    totalRecommendedTests: 0,
    totalClusters: testRecommendations.length,
    categoryCounts: {},
    complexityDistribution: {}
  };

  testRecommendations.forEach(test => {
    stats.totalStandardTests += (test.standard_tests || []).length;
    stats.totalRecommendedTests += (test.recommended_tests || []).length;

    // Count categories
    const categories = test.test_metadata?.testCategories || {};
    Object.keys(categories).forEach(category => {
      stats.categoryCounts[category] = (stats.categoryCounts[category] || 0) + categories[category].length;
    });
  });

  return stats;
}

function aggregateAndDeduplicateTests(testRecommendations) {
  const allStandardTests = new Set();
  const allRecommendedTests = new Set();
  const testsByCategory = {};

  testRecommendations.forEach(test => {
    // Add standard tests
    (test.standard_tests || []).forEach(testItem => {
      allStandardTests.add(testItem);
    });

    // Add recommended tests
    (test.recommended_tests || []).forEach(testItem => {
      allRecommendedTests.add(testItem);
    });

    // Aggregate by category
    const categories = test.test_metadata?.testCategories || {};
    Object.entries(categories).forEach(([category, tests]) => {
      if (!testsByCategory[category]) {
        testsByCategory[category] = new Set();
      }
      tests.forEach(testItem => testsByCategory[category].add(testItem));
    });
  });

  // Convert sets back to arrays
  const result = {
    standardTests: Array.from(allStandardTests),
    recommendedTests: Array.from(allRecommendedTests),
    testsByCategory: {}
  };

  Object.entries(testsByCategory).forEach(([category, testSet]) => {
    result.testsByCategory[category] = Array.from(testSet);
  });

  return result;
}

function organizeTestsByCategory(testRecommendations) {
  const organized = {};

  testRecommendations.forEach(test => {
    const categories = test.test_metadata?.testCategories || {};
    
    Object.entries(categories).forEach(([category, tests]) => {
      if (!organized[category]) {
        organized[category] = {
          standardTests: [],
          recommendedTests: [],
          clusters: []
        };
      }

      organized[category].clusters.push({
        clusterId: test.cluster_id,
        summary: test.cluster_summary,
        tests: tests
      });
    });

    // Also categorize standard and recommended tests
    (test.standard_tests || []).forEach(testItem => {
      const category = inferTestCategory(testItem);
      if (!organized[category]) {
        organized[category] = { standardTests: [], recommendedTests: [], clusters: [] };
      }
      organized[category].standardTests.push(testItem);
    });

    (test.recommended_tests || []).forEach(testItem => {
      const category = inferTestCategory(testItem);
      if (!organized[category]) {
        organized[category] = { standardTests: [], recommendedTests: [], clusters: [] };
      }
      organized[category].recommendedTests.push(testItem);
    });
  });

  return organized;
}

function inferTestCategory(testDescription) {
  const lowerTest = testDescription.toLowerCase();
  
  if (lowerTest.includes('performance') || lowerTest.includes('load') || lowerTest.includes('stress')) {
    return 'performance';
  }
  if (lowerTest.includes('security') || lowerTest.includes('auth') || lowerTest.includes('permission')) {
    return 'security';
  }
  if (lowerTest.includes('usability') || lowerTest.includes('ui') || lowerTest.includes('ux')) {
    return 'usability';
  }
  if (lowerTest.includes('api') || lowerTest.includes('endpoint') || lowerTest.includes('integration')) {
    return 'api';
  }
  if (lowerTest.includes('accessibility') || lowerTest.includes('wcag') || lowerTest.includes('screen reader')) {
    return 'accessibility';
  }
  
  return 'functional';
}

function convertToCSV(testRecommendations) {
  const headers = ['Cluster ID', 'Feature Category', 'Summary', 'Test Type', 'Test Description'];
  const rows = [headers.join(',')];

  testRecommendations.forEach(test => {
    const category = test.cluster_summaries?.[0]?.feature_category || 'General';
    
    (test.standard_tests || []).forEach(testDesc => {
      rows.push([
        test.cluster_id,
        category,
        `"${test.cluster_summary?.replace(/"/g, '""') || ''}"`,
        'Standard',
        `"${testDesc.replace(/"/g, '""')}"`
      ].join(','));
    });

    (test.recommended_tests || []).forEach(testDesc => {
      rows.push([
        test.cluster_id,
        category,
        `"${test.cluster_summary?.replace(/"/g, '""') || ''}"`,
        'Recommended',
        `"${testDesc.replace(/"/g, '""')}"`
      ].join(','));
    });
  });

  return rows.join('\n');
}

function convertToMarkdown(testRecommendations) {
  let markdown = '# Test Recommendations Report\n\n';
  
  testRecommendations.forEach(test => {
    const category = test.cluster_summaries?.[0]?.feature_category || 'General';
    
    markdown += `## Cluster ${test.cluster_id}: ${category}\n\n`;
    markdown += `**Summary:** ${test.cluster_summary || 'No summary available'}\n\n`;
    
    markdown += '### Standard Tests\n\n';
    (test.standard_tests || []).forEach((testDesc, index) => {
      markdown += `${index + 1}. ${testDesc}\n`;
    });
    
    markdown += '\n### Recommended Tests\n\n';
    (test.recommended_tests || []).forEach((testDesc, index) => {
      markdown += `${index + 1}. ${testDesc}\n`;
    });
    
    markdown += '\n---\n\n';
  });

  return markdown;
}

module.exports = router;