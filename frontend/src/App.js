import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [brdContent, setBrdContent] = useState('');
  const [jiraConfig, setJiraConfig] = useState({
    email: '',
    token: '',
    project_name: '',
    sprint_id: '',
    assigned_to_me: false,
    epic: ''
  });
  
  // New states for enhanced Jira integration
  const [jiraUrl, setJiraUrl] = useState('');
  const [issueType, setIssueType] = useState('all');
  const [jiraIssues, setJiraIssues] = useState([]);
  const [userStories, setUserStories] = useState([]);
  const [fetchedUserStories, setFetchedUserStories] = useState(false);
  const [jiraSessionId, setJiraSessionId] = useState('');
  const [savedBrdFiles, setSavedBrdFiles] = useState([]);
  const [showSavedFiles, setShowSavedFiles] = useState(false);
  const [showIssues, setShowIssues] = useState(false);
  
  const [comparisonResult, setComparisonResult] = useState(null);
  const [testRecommendations, setTestRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jiraLoading, setJiraLoading] = useState(false);
  const [processingLoading, setProcessingLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('full');
  const [currentStep, setCurrentStep] = useState(1); // Track workflow step
  const [documentIds, setDocumentIds] = useState({ brd: null, userStories: null });

  // Add a function to fetch saved BRD files
  const fetchSavedBrdFiles = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/brd-files`);
      if (response.data && response.data.files) {
        setSavedBrdFiles(response.data.files);
        setShowSavedFiles(true);
      }
    } catch (error) {
      console.error('Error fetching saved BRD files:', error);
      toast.error('Failed to fetch saved BRD files');
    }
  };
  
  // Modify the onDrop function to work with the updated backend
  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      try {
        const formData = new FormData();
        formData.append('file', file);

        toast.info('Uploading BRD file...');
        const response = await axios.post(`${API_BASE_URL}/upload-brd`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data && response.data.content) {
          setBrdContent(response.data.content);
          toast.success('BRD file uploaded and processed successfully!');
          setCurrentStep(2); // Move to Jira configuration step
        }
      } catch (error) {
        console.error('Error uploading BRD:', error);
        toast.error(`Error uploading BRD: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  // Initialize the useDropzone hook
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    multiple: false
  });
  
  // Function to load a saved BRD file
  const loadSavedBrdFile = async (filename) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/brd-file/${filename}`);
      if (response.data && response.data.content) {
        setBrdContent(response.data.content);
        setShowSavedFiles(false);
        toast.success('BRD file loaded successfully!');
        setCurrentStep(2); // Move to Jira configuration step
      }
    } catch (error) {
      console.error('Error loading BRD file:', error);
      toast.error(`Error loading BRD file: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setJiraConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  const generateSessionId = () => {
    return `session-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  };
  
  const fetchJiraIssues = async () => {
    if (!jiraConfig.email || !jiraConfig.token || !jiraConfig.project_name || !jiraConfig.sprint_id) {
      toast.error('Please fill in all required Jira fields');
      return;
    }
    
    if (!jiraUrl) {
      toast.error('Please provide your Jira URL (e.g., https://your-domain.atlassian.net)');
      return;
    }
    
    setJiraLoading(true);
    try {
      const sessionId = generateSessionId();
      setJiraSessionId(sessionId);
      
      toast.info('Fetching Jira issues...');
      const response = await axios.post(`${API_BASE_URL}/api/jira-auth`, {
        email: jiraConfig.email,
        apiToken: jiraConfig.token,
        jiraUrl: jiraUrl,
        project: jiraConfig.project_name,
        sprint: jiraConfig.sprint_id,
        epic: jiraConfig.epic || undefined,
        filterByAssignee: jiraConfig.assigned_to_me,
        issueType: issueType
      });
      
      if (response.data.success) {
        setJiraIssues(response.data.issues);
        toast.success(`Fetched ${response.data.issues.length} issues from Jira`);
        setCurrentStep(3); // Move to process user stories step
        
        // Automatically process user stories
        await processJiraIssuesAutomatically(response.data.issues, sessionId);
      } else {
        toast.error('Failed to fetch Jira issues');
      }
    } catch (error) {
      toast.error(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setJiraLoading(false);
    }
  };
  
  const processJiraIssuesAutomatically = async (issues, sessionId) => {
    if (!issues || !issues.length) {
      toast.error('No Jira issues to process');
      return;
    }
    
    setProcessingLoading(true);
    try {
      toast.info('Processing user stories...');
      
      const response = await axios.post(`${API_BASE_URL}/api/process-jira-issues`, {
        session_id: sessionId,
        issues: issues,
        project: jiraConfig.project_name
      });
      
      setUserStories(response.data.user_stories);
      setFetchedUserStories(true);
      toast.success(`Processed ${response.data.user_stories.length} user stories`);
      setCurrentStep(4); // Move directly to gap analysis step
    } catch (error) {
      toast.error(`Error processing user stories: ${error.response?.data?.detail || error.message}`);
    } finally {
      setProcessingLoading(false);
    }
  };

  const handleGapAnalysis = async () => {
    if (!brdContent) {
      toast.error('Please upload a BRD document first');
      return;
    }

    if (!fetchedUserStories || !userStories.length) {
      toast.error('Please fetch and process Jira user stories first');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/compare`, {
        brd_content: brdContent,
        user_stories: userStories
      });
      
      setComparisonResult(response.data);
      toast.success('Gap analysis completed successfully!');
      setCurrentStep(5); // Move to test recommendations step
    } catch (error) {
      toast.error(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const generateTestRecommendations = async () => {
    // Check if there are missing requirements before generating
    if (comparisonResult?.gap_analysis?.has_gaps || extractMissingRequirements().length > 0) {
      toast.error('Cannot generate test recommendations while there are missing requirements. Please address the gaps first.');
      return;
    }

    try {
      setTestLoading(true);
      toast.info('Generating intelligent test recommendations...');

      // First upload BRD content as text
      const brdResponse = await axios.post(`${API_BASE_URL}/api/documents/upload-text`, {
        content: brdContent
      });

      if (!brdResponse.data.success) {
        throw new Error('Failed to upload BRD content');
      }

      const brdDocumentId = brdResponse.data.document_id;

      // Upload user stories as text content
      const userStoriesContent = userStories.map(story => 
        `${story.title}\n${story.description}\nJira Key: ${story.jira_key || 'N/A'}\nStatus: ${story.status || 'Unknown'}`
      ).join('\n\n---\n\n');

      const userStoriesResponse = await axios.post(`${API_BASE_URL}/api/documents/upload-text`, {
        content: userStoriesContent
      });

      if (!userStoriesResponse.data.success) {
        throw new Error('Failed to upload user stories content');
      }

      const userStoriesDocumentId = userStoriesResponse.data.document_id;

      // Generate intelligent test recommendations using the integrated system
      const testResponse = await axios.post(`${API_BASE_URL}/api/tests/generate-intelligent`, {
        brd_document_id: brdDocumentId,
        user_stories_document_id: userStoriesDocumentId
      });

      setTestRecommendations(testResponse.data);
      setDocumentIds({ brd: brdDocumentId, userStories: userStoriesDocumentId });
      toast.success(`Generated ${testResponse.data.recommendations.length} test recommendations clusters!`);
      
    } catch (error) {
      console.error('Error generating test recommendations:', error);
      toast.error(`Error generating test recommendations: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestLoading(false);
    }
  };

  // Enhanced function to extract missing requirements from comparison result
  const extractMissingRequirements = () => {
    if (comparisonResult?.missing_requirements && comparisonResult.missing_requirements.length > 0) {
      return comparisonResult.missing_requirements.map(req => req.trim()).filter(req => req.length > 0);
    }
    
    if (!comparisonResult?.comparison_result) return [];
    
    const result = comparisonResult.comparison_result;
    
    const missingReqsHeader = "## MISSING REQUIREMENTS";
    if (result.includes(missingReqsHeader)) {
      const missingSection = result.split(missingReqsHeader)[1];
      if (!missingSection) return [];
      
      const lines = missingSection.split('\n');
      const missingReqs = [];
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.match(/^\d+\.\s+/)) {
          const requirement = trimmedLine.replace(/^\d+\.\s+/, '').trim();
          if (requirement && !requirement.toLowerCase().includes('no specific missing requirements')) {
            missingReqs.push(requirement);
          }
        }
      }
      
      return missingReqs;
    }
    
    return [];
  };
  
  const toggleIssuesView = () => {
    setShowIssues(prev => !prev);
  };

  // Helper function to convert markdown to HTML with improved formatting
  const formatMarkdownText = (text) => {
    if (!text) return '';
    
    let formattedText = text;
    
    formattedText = formattedText.replace(/^##\s+(.*)$/gm, '<h2>$1</h2>');
    formattedText = formattedText.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>');
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    formattedText = formattedText.replace(/(?:^\d+\.\s+.*$(?:\n(?!\n|##\s+|###\s+).*$)*)/gm, function(match) {
      const items = match.split('\n').map(line => {
        if (line.trim().match(/^\d+\.\s+/)) {
          return `<li>${line.replace(/^\d+\.\s+/, '').trim()}</li>`;
        }
        return line.trim() ? `<li>${line.trim()}</li>` : '';
      }).filter(item => item).join('');
      return `<ol class="compact-list">${items}</ol>`;
    });
    
    formattedText = formattedText.replace(/(?:^[*-]\s+.*$(?:\n(?!\n|##\s+|###\s+).*$)*)/gm, function(match) {
      const items = match.split('\n').map(line => {
        if (line.trim().match(/^[*-]\s+/)) {
          return `<li>${line.replace(/^[*-]\s+/, '').trim()}</li>`;
        }
        return line.trim() ? `<li>${line.trim()}</li>` : '';
      }).filter(item => item).join('');
      return `<ul class="compact-list">${items}</ul>`;
    });
    
    formattedText = formattedText.replace(/^([^<\n].*?)$/gm, (match) => {
      if (match.trim() && !match.includes('<')) {
        return `<p>${match}</p>`;
      }
      return match;
    });
    
    formattedText = formattedText.replace(/\n{3,}/g, '\n\n');
    
    return formattedText;
  };

  // Step progress indicator
  const renderStepIndicator = () => {
    const steps = [
      { num: 1, title: "Upload BRD", completed: currentStep > 1 },
      { num: 2, title: "Configure Jira", completed: currentStep > 2 },
      { num: 3, title: "Process Stories", completed: currentStep > 3 },
      { num: 4, title: "Gap Analysis", completed: currentStep > 4 },
      { num: 5, title: "Test Recommendations", completed: currentStep > 5 }
    ];

    return (
      <div className="step-indicator">
        {steps.map((step, index) => (
          <div key={step.num} className={`step ${currentStep === step.num ? 'active' : ''} ${step.completed ? 'completed' : ''}`}>
            <div className="step-number">{step.num}</div>
            <div className="step-title">{step.title}</div>
            {index < steps.length - 1 && <div className="step-connector"></div>}
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div className="App">
      <header className="App-header">
        <h1>Intelligent Test Recommendation System</h1>
        <p>BRD Analysis → Jira Integration → Gap Analysis → Test Recommendations</p>
      </header>

      {renderStepIndicator()}

      <main className="main-content">
        {/* Step 1: BRD Upload */}
        <div className={`workflow-section ${currentStep === 1 ? 'active' : currentStep > 1 ? 'completed' : 'disabled'}`}>
          <div className="upload-section">
            <h2>Step 1: Upload BRD Document</h2>
            <div className="upload-actions">
              <button 
                onClick={fetchSavedBrdFiles}
                className="saved-files-btn"
              >
                View Saved BRDs
              </button>
            </div>
            
            {showSavedFiles && savedBrdFiles.length > 0 && (
              <div className="saved-files-list">
                <h3>Saved BRD Files</h3>
                <div className="files-grid">
                  {savedBrdFiles.map((file, index) => (
                    <div key={index} className="file-card" onClick={() => loadSavedBrdFile(file.filename)}>
                      <div className="file-icon">📄</div>
                      <div className="file-details">
                        <div className="file-name">{file.original_name || file.filename}</div>
                        <div className="file-info">
                          <span>Created: {new Date(file.created).toLocaleDateString()}</span>
                          <span>Size: {Math.round(file.size / 1024)} KB</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={() => setShowSavedFiles(false)}
                  className="close-btn"
                >
                  Close
                </button>
              </div>
            )}
            
            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
              <input {...getInputProps()} />
              {isDragActive ? (
                <p>Drop the BRD file here...</p>
              ) : (
                <p>Drag & drop a BRD file here, or click to select</p>
              )}
            </div>

            {brdContent && (
              <div className="file-preview">
                <h3>BRD Content Preview:</h3>
                <div className="preview-controls">
                  <button 
                    onClick={() => document.getElementById('preview-textarea').classList.toggle('full-height')}
                    className="toggle-preview-btn"
                  >
                    {document.getElementById('preview-textarea')?.classList.contains('full-height') 
                      ? 'Show Less' 
                      : 'Show Full Content'}
                  </button>
                </div>
                <textarea 
                  id="preview-textarea"
                  value={brdContent}
                  readOnly
                  rows={8}
                  className="preview-textarea"
                />
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Jira Configuration */}
        <div className={`workflow-section ${currentStep === 2 ? 'active' : currentStep > 2 ? 'completed' : 'disabled'}`}>
          <div className="jira-config-section">
            <h2>Step 2: Configure Jira Integration</h2>
            <div className="config-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={jiraConfig.email}
                    onChange={handleInputChange}
                    placeholder="your-email@company.com"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Jira Token *</label>
                  <input
                    type="password"
                    name="token"
                    value={jiraConfig.token}
                    onChange={handleInputChange}
                    placeholder="Your Jira API token"
                    required
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Jira URL *</label>
                <input
                  type="text"
                  value={jiraUrl}
                  onChange={(e) => setJiraUrl(e.target.value)}
                  placeholder="https://your-domain.atlassian.net"
                  required
                />
                <small className="form-helper-text">
                  Enter your complete Atlassian URL (not just the project key)
                </small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Project Name *</label>
                  <input
                    type="text"
                    name="project_name"
                    value={jiraConfig.project_name}
                    onChange={handleInputChange}
                    placeholder="PROJECT_KEY"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Sprint ID/Name *</label>
                  <input
                    type="text"
                    name="sprint_id"
                    value={jiraConfig.sprint_id}
                    onChange={handleInputChange}
                    placeholder="Sprint 123 or 123"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Epic (Optional)</label>
                  <input
                    type="text"
                    name="epic"
                    value={jiraConfig.epic}
                    onChange={handleInputChange}
                    placeholder="EPIC-123"
                  />
                </div>
                
                <div className="form-group">
                  <label>Issue Type</label>
                  <select
                    value={issueType}
                    onChange={(e) => setIssueType(e.target.value)}
                  >
                    <option value="all">All Types</option>
                    <option value="story">User Stories</option>
                    <option value="bug">Bugs</option>
                    <option value="task">Tasks</option>
                    <option value="epic">Epics</option>
                  </select>
                </div>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    name="assigned_to_me"
                    checked={jiraConfig.assigned_to_me}
                    onChange={handleInputChange}
                  />
                  Show only assigned to me
                </label>
              </div>
            </div>
            
            <div className="action-center">
              <button 
                onClick={fetchJiraIssues} 
                disabled={jiraLoading || currentStep < 2}
                className="primary-button"
              >
                {jiraLoading ? 'Fetching Issues...' : 'Fetch Jira Issues'}
              </button>
            </div>
          </div>
        </div>

        {/* Step 3: Process User Stories - Now Automatic */}
        {jiraIssues.length > 0 && (
          <div className={`workflow-section ${currentStep === 3 ? 'active' : currentStep > 3 ? 'completed' : 'disabled'}`}>
            <div className="jira-issues-section">
              <h2>Step 3: Jira Issues & User Stories Processing</h2>
              <div className="jira-issues-summary">
                <p>✅ Fetched {jiraIssues.length} issues from Jira</p>
                {fetchedUserStories && (
                  <p>✅ Processed {userStories.length} user stories automatically</p>
                )}
                {processingLoading && (
                  <p>🔄 Processing user stories...</p>
                )}
                <button 
                  className="toggle-issues-btn"
                  onClick={toggleIssuesView}
                >
                  {showIssues ? 'Hide Issues' : 'Show Issues'} ▾
                </button>
              </div>
              
              {showIssues && (
                <div className="issues-container">
                  <div className="issues-grid">
                    {jiraIssues.map((issue, index) => (
                      <div key={index} className="issue-card">
                        <div className="issue-header">
                          <span className="issue-key">{issue.key}</span>
                          <span className={`issue-type ${issue.fields?.issuetype?.name.toLowerCase().replace(' ', '-')}`}>
                            {issue.fields?.issuetype?.name}
                          </span>
                        </div>
                        <h4 className="issue-title">{issue.fields?.summary}</h4>
                        <div className="issue-meta">
                          <div className="issue-status">
                            <span className="meta-label">Status:</span> 
                            <span className={`status-tag ${issue.fields?.status?.name.toLowerCase().replace(' ', '-')}`}>
                              {issue.fields?.status?.name}
                            </span>
                          </div>
                          <div className="issue-assignee">
                            <span className="meta-label">Assignee:</span> 
                            {issue.fields?.assignee?.displayName || 'Unassigned'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 4: Gap Analysis (Automatic after user story processing) */}
        {fetchedUserStories && (
          <div className={`workflow-section ${currentStep === 4 ? 'active' : currentStep > 4 ? 'completed' : 'disabled'}`}>
            <div className="gap-analysis-section">
              <h2>Step 4: Requirements Gap Analysis</h2>
              <div className="user-stories-summary">
                <p>Processed {userStories.length} user stories ready for analysis</p>
              </div>
              
              <div className="action-center">
                <button 
                  onClick={handleGapAnalysis} 
                  disabled={loading || currentStep < 4}
                  className="primary-button gap-analysis-btn"
                >
                  {loading ? 'Analyzing Gaps...' : 'Perform Gap Analysis'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Show Gap Analysis Results */}
        {comparisonResult && (
          <div className={`workflow-section ${currentStep >= 4 ? 'active' : 'disabled'}`}>
            <div className="results-section">
              <h2>Gap Analysis Results</h2>
              
              <div className="results-tabs">
                <button 
                  className={`tab-button ${activeTab === 'full' ? 'active' : ''}`} 
                  onClick={() => setActiveTab('full')}
                >
                  Full Analysis
                </button>
                <button 
                  className={`tab-button ${activeTab === 'missing' ? 'active' : ''}`} 
                  onClick={() => setActiveTab('missing')}
                >
                  Missing Requirements
                </button>
                <button 
                  className={`tab-button ${activeTab === 'brd' ? 'active' : ''}`} 
                  onClick={() => setActiveTab('brd')}
                >
                  BRD Analysis
                </button>
                <button 
                  className={`tab-button ${activeTab === 'stories' ? 'active' : ''}`} 
                  onClick={() => setActiveTab('stories')}
                >
                  User Stories
                </button>
              </div>
              
              {activeTab === 'full' && (
                <div className="gap-analysis-section tab-content">
                  <div className="result-section">
                    <h3>Full Comparison Analysis</h3>
                    <div 
                      className="result-content"
                      dangerouslySetInnerHTML={{ __html: formatMarkdownText(comparisonResult.comparison_result) }}
                    />
                  </div>
                </div>
              )}
              
              {activeTab === 'missing' && (
                <div className="gap-analysis-section missing-requirements-section tab-content">
                  <div className="result-section">
                    <h3>Missing Requirements</h3>
                    <div className="result-content missing-requirements">
                      {extractMissingRequirements().length > 0 ? (
                        <>
                          <p className="requirements-intro">The following BRD requirements are not covered by the current user stories:</p>
                          <div className="missing-list-container">
                            <ol className="missing-list">
                              {extractMissingRequirements().map((req, idx) => (
                                <li key={idx} className="missing-requirement-item">
                                  <div 
                                    className="requirement-content"
                                    dangerouslySetInnerHTML={{ __html: formatMarkdownText(req) }}
                                  />
                                </li>
                              ))}
                            </ol>
                          </div>
                        </>
                      ) : (
                        <div className="complete-coverage">
                          <div className="success-icon">✓</div>
                          <h4>Complete Coverage</h4>
                          <p>Excellent! All BRD requirements appear to be covered by the user stories. No gaps were identified in the comparison.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {activeTab === 'brd' && (
                <div className="gap-analysis-section brd-analysis-section tab-content">
                  <div className="result-section">
                    <h3>BRD Analysis</h3>
                    <div 
                      className="result-content"
                      dangerouslySetInnerHTML={{ __html: formatMarkdownText(comparisonResult.brd_analysis) }}
                    />
                  </div>
                </div>
              )}
              
              {activeTab === 'stories' && (
                <div className="tab-content">
                  <div className="result-section">
                    <h3>User Stories ({userStories.length})</h3>
                    <div className="stories-grid in-results">
                      {userStories.map((story, index) => (
                        <div key={index} className="story-card">
                          <h4>{story.id}: {story.title}</h4>
                          <p className="story-description">
                            {typeof story.description === 'string' ? 
                              (story.description.length > 150 ? 
                                `${story.description.substring(0, 150)}...` : story.description) : 
                              "Complex description (see Jira)"}
                          </p>
                          {story.acceptance_criteria?.length > 0 && (
                            <div className="acceptance-criteria">
                              <strong>Acceptance Criteria:</strong>
                              <ul>
                                {story.acceptance_criteria.map((criteria, i) => (
                                  <li key={i}>{criteria.substring(0, 100)}{criteria.length > 100 ? '...' : ''}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Test Recommendations Trigger or Gap Analysis Warning */}
              {(comparisonResult?.gap_analysis?.has_gaps || extractMissingRequirements().length > 0) ? (
                // Show gap analysis warning instead of button - NO purple background
                <div className="gap-analysis-warning">
                  <div className="gap-warning-header">
                    <h3>⚠️ Missing Requirements Detected</h3>
                    <p>Critical requirements are missing from the BRD/User Stories. Please address these gaps before generating test recommendations.</p>
                  </div>
                  
                  <div className="gap-details">
                    <h4>Missing Requirements:</h4>
                    <ul>
                      {extractMissingRequirements().length > 0 ? (
                        extractMissingRequirements().map((req, index) => (
                          <li key={index}>{req}</li>
                        ))
                      ) : (
                        comparisonResult.gap_analysis?.missing_requirements?.map((req, index) => (
                          <li key={index}>{req}</li>
                        ))
                      )}
                    </ul>
                    
                    <div className="gap-description">
                      <h4>Details:</h4>
                      <p>
                        {extractMissingRequirements().length > 0 
                          ? "The following BRD requirements are not covered by the current user stories. Please update your documentation to include these requirements."
                          : comparisonResult.gap_analysis?.gap_details
                        }
                      </p>
                    </div>
                    
                    <div className="gap-recommendations">
                      <h4>Recommendations:</h4>
                      <ul>
                        <li>Review and update your BRD to include the missing requirements</li>
                        <li>Add user stories that cover the missing functionality</li>
                        <li>Ensure all critical business requirements are documented</li>
                        <li>Re-upload the updated documents to proceed with test recommendations</li>
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                // Only show button if NO gaps detected anywhere
                !(testRecommendations?.gap_analysis?.has_gaps || testRecommendations?.has_gap_issues) && (
                  <div className="test-recommendations-trigger">
                    <h3>Generate Test Recommendations</h3>
                    <p>Based on the gap analysis, generate intelligent test recommendations using AI.</p>
                    <button 
                      onClick={generateTestRecommendations}
                      disabled={testLoading}
                      className="primary-button test-recommendations-btn"
                    >
                      {testLoading ? 'Generating Test Recommendations...' : 'Show Testing Type Recommendations'}
                    </button>
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* Test Recommendations Results */}
        {testRecommendations && (
          <div className="workflow-section active">
            <div className="test-recommendations-section">
              <h2>Intelligent Test Recommendations</h2>
              
              {/* Check if gap analysis detected missing requirements */}
              {(testRecommendations.gap_analysis?.has_gaps || testRecommendations.has_gap_issues) ? (
                <div className="gap-analysis-warning">
                  <div className="gap-warning-header">
                    <h3>⚠️ Missing Requirements Detected</h3>
                    <p>Critical requirements are missing from the BRD/User Stories. Please address these gaps before generating test recommendations.</p>
                  </div>
                  
                  <div className="gap-details">
                    <h4>Missing Requirements:</h4>
                    <ul>
                      {testRecommendations.gap_analysis.missing_requirements?.map((req, index) => (
                        <li key={index}>{req}</li>
                      ))}
                    </ul>
                    
                    <div className="gap-description">
                      <h4>Details:</h4>
                      <p>{testRecommendations.gap_analysis.gap_details}</p>
                    </div>
                    
                    <div className="gap-recommendations">
                      <h4>Recommendations:</h4>
                      <ul>
                        <li>Review and update your BRD to include the missing requirements</li>
                        <li>Add user stories that cover the missing functionality</li>
                        <li>Ensure all critical business requirements are documented</li>
                        <li>Re-upload the updated documents to generate test recommendations</li>
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  <div className="recommendations-summary">
                    <div className="summary-stats">
                      <div className="stat-card">
                        <span className="stat-number">1</span>
                        <span className="stat-label">Test Analysis</span>
                      </div>
                      <div className="stat-card">
                        <span className="stat-number">
                          {(() => {
                            const allTests = testRecommendations.recommendations?.reduce((acc, cluster) => 
                              acc.concat(cluster.tests || []), []) || [];
                            return allTests.filter(test => 
                              test.category?.toLowerCase() === 'standard' || 
                              test.test_classification === 'STANDARD'
                            ).length;
                          })()}
                        </span>
                        <span className="stat-label">Standard Tests</span>
                      </div>
                      <div className="stat-card">
                        <span className="stat-number">
                          {(() => {
                            const allTests = testRecommendations.recommendations?.reduce((acc, cluster) => 
                              acc.concat(cluster.tests || []), []) || [];
                            return allTests.filter(test => 
                              test.category?.toLowerCase() === 'recommended' || 
                              test.test_classification === 'RECOMMENDED'
                            ).length;
                          })()}
                        </span>
                        <span className="stat-label">Recommended Tests</span>
                      </div>
                      <div className="stat-card">
                        <span className="stat-number">100%</span>
                        <span className="stat-label">Domain Match</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="recommendations-container">
                    {testRecommendations.recommendations && Array.isArray(testRecommendations.recommendations) ? (
                      <div className="all-tests-sections">
                        {/* Collect all tests from all clusters */}
                        {(() => {
                          const allTests = testRecommendations.recommendations.flatMap(cluster => 
                            cluster.tests && Array.isArray(cluster.tests) ? cluster.tests : []
                          );

                          const standardTests = allTests.filter(test => 
                            test.category?.toLowerCase() === 'standard' || 
                            test.test_classification === 'STANDARD'
                          );

                          const recommendedTests = allTests.filter(test => 
                            test.category?.toLowerCase() === 'recommended' || 
                            test.test_classification === 'RECOMMENDED'
                      );

                      return (
                        <div className="simple-test-results">
                          {/* Standard Tests Card */}
                          {standardTests.length > 0 && (
                            <div className="simple-test-card">
                              <h3 className="card-title standard">
                                � Standard Testing ({standardTests.length})
                              </h3>
                              <div className="simple-test-list">
                                {standardTests.map((test, testIndex) => {
                                  console.log('Standard test data:', test); // Debug log
                                  
                                  // Extract source story from rationale if not in source_story field
                                  let sourceStory = test.source_story;
                                  if (!sourceStory && test.rationale) {
                                    const match = test.rationale.match(/ZB-\d+/);
                                    sourceStory = match ? match[0] : null;
                                  }
                                  
                                  return (
                                    <div key={testIndex} className="simple-test-item">
                                      <div className="test-name">{test.name || test.test_name}</div>
                                      <div className="test-source">
                                        From: {sourceStory || test.cluster_attribution || 'Analysis Engine'}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}

                          {/* Recommended Tests Card */}
                          {recommendedTests.length > 0 && (
                            <div className="simple-test-card">
                              <h3 className="card-title recommended">
                                🎯 Recommended Testing ({recommendedTests.length})
                              </h3>
                              <div className="simple-test-list">
                                {recommendedTests.map((test, testIndex) => {
                                  console.log('Recommended test data:', test); // Debug log
                                  
                                  // Extract source story from rationale if not in source_story field
                                  let sourceStory = test.source_story;
                                  if (!sourceStory && test.rationale) {
                                    const match = test.rationale.match(/ZB-\d+/);
                                    sourceStory = match ? match[0] : null;
                                  }
                                  
                                  return (
                                    <div key={testIndex} className="simple-test-item">
                                      <div className="test-name">{test.name || test.test_name}</div>
                                      <div className="test-source">
                                        From: {sourceStory || test.cluster_attribution || 'Analysis Engine'}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                ) : (
                  <p>No test recommendations available.</p>
                )}
              </div>
              </>
              )}
            </div>
          </div>
        )}

      </main>

      <ToastContainer 
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick={true}
        rtl={false}
        pauseOnFocusLoss={true}
        draggable={true}
        pauseOnHover={true}
      />
    </div>
  );
}

export default App;
