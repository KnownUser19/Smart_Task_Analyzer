/**
 * Smart Task Analyzer - Frontend Application
 * 
 * This module handles all frontend interactions including:
 * - Task input (form and JSON modes)
 * - Strategy selection
 * - API communication
 * - Results rendering
 * 
 * Author: Candidate for Software Development Intern Position
 */

// ============================================
// Configuration
// ============================================

// Auto-detect API URL: Use relative path in production, localhost in development
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const CONFIG = {
    API_BASE_URL: isLocalhost ? 'http://localhost:8000/api' : '/api',
    ENDPOINTS: {
        ANALYZE: '/tasks/analyze/',
        SUGGEST: '/tasks/suggest/',
        VALIDATE: '/tasks/validate/'
    }
};

// ============================================
// State Management
// ============================================

const state = {
    tasks: [],
    currentStrategy: 'smart_balance',
    inputMode: 'form',
    isLoading: false,
    lastAnalysisResult: null
};

// ============================================
// Sample Data
// ============================================

const SAMPLE_TASKS = [
    {
        id: "task_1",
        title: "Fix critical login authentication bug",
        due_date: getTodayPlusDays(1),
        estimated_hours: 3,
        importance: 9,
        dependencies: []
    },
    {
        id: "task_2",
        title: "Update user documentation",
        due_date: getTodayPlusDays(7),
        estimated_hours: 2,
        importance: 5,
        dependencies: ["task_1"]
    },
    {
        id: "task_3",
        title: "Implement new dashboard feature",
        due_date: getTodayPlusDays(14),
        estimated_hours: 8,
        importance: 7,
        dependencies: []
    },
    {
        id: "task_4",
        title: "Quick CSS fix for mobile nav",
        due_date: getTodayPlusDays(3),
        estimated_hours: 0.5,
        importance: 4,
        dependencies: []
    },
    {
        id: "task_5",
        title: "Database optimization query review",
        due_date: getTodayPlusDays(-2),
        estimated_hours: 4,
        importance: 8,
        dependencies: []
    },
    {
        id: "task_6",
        title: "API rate limiting implementation",
        due_date: getTodayPlusDays(5),
        estimated_hours: 6,
        importance: 8,
        dependencies: ["task_1"]
    }
];

// ============================================
// Utility Functions
// ============================================

function getTodayPlusDays(days) {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date.toISOString().split('T')[0];
}

function generateTaskId() {
    return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function formatDate(dateString) {
    if (!dateString) return 'No due date';
    const date = new Date(dateString);
    const options = { month: 'short', day: 'numeric', year: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// DOM Elements
// ============================================

const elements = {
    // Input mode toggle
    toggleBtns: document.querySelectorAll('.toggle-btn'),
    formMode: document.getElementById('form-mode'),
    jsonMode: document.getElementById('json-mode'),
    
    // Form inputs
    taskTitle: document.getElementById('task-title'),
    taskDue: document.getElementById('task-due'),
    taskHours: document.getElementById('task-hours'),
    taskImportance: document.getElementById('task-importance'),
    importanceDisplay: document.getElementById('importance-display'),
    taskDependencies: document.getElementById('task-dependencies'),
    addTaskBtn: document.getElementById('add-task-btn'),
    
    // Task list
    taskList: document.getElementById('task-list'),
    taskCount: document.getElementById('task-count'),
    emptyState: document.getElementById('empty-state'),
    clearTasksBtn: document.getElementById('clear-tasks-btn'),
    
    // JSON input
    jsonInput: document.getElementById('json-input'),
    loadSampleBtn: document.getElementById('load-sample-btn'),
    parseJsonBtn: document.getElementById('parse-json-btn'),
    
    // Strategy
    strategyCards: document.querySelectorAll('.strategy-card'),
    
    // Analyze
    analyzeBtn: document.getElementById('analyze-btn'),
    
    // Results
    resultsSection: document.getElementById('results-section'),
    resultsMeta: document.getElementById('results-meta'),
    resultsGrid: document.getElementById('results-grid'),
    priorityDistribution: document.getElementById('priority-distribution'),
    circularWarning: document.getElementById('circular-warning'),
    circularDetails: document.getElementById('circular-details'),
    getSuggestionsBtn: document.getElementById('get-suggestions-btn'),
    
    // Distribution
    distHigh: document.getElementById('dist-high'),
    distMedium: document.getElementById('dist-medium'),
    distLow: document.getElementById('dist-low'),
    countHigh: document.getElementById('count-high'),
    countMedium: document.getElementById('count-medium'),
    countLow: document.getElementById('count-low'),
    
    // Modal
    suggestionsModal: document.getElementById('suggestions-modal'),
    closeModal: document.getElementById('close-modal'),
    suggestionsContent: document.getElementById('suggestions-content')
};

// ============================================
// Event Listeners Setup
// ============================================

function setupEventListeners() {
    // Input mode toggle
    elements.toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => handleModeToggle(btn.dataset.mode));
    });
    
    // Form inputs
    elements.taskImportance.addEventListener('input', updateImportanceDisplay);
    elements.addTaskBtn.addEventListener('click', handleAddTask);
    elements.clearTasksBtn.addEventListener('click', handleClearTasks);
    
    // JSON inputs
    elements.loadSampleBtn.addEventListener('click', handleLoadSample);
    elements.parseJsonBtn.addEventListener('click', handleParseJson);
    
    // Strategy selection
    elements.strategyCards.forEach(card => {
        card.addEventListener('click', () => handleStrategySelect(card));
    });
    
    // Analyze button
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    
    // Suggestions
    elements.getSuggestionsBtn.addEventListener('click', handleGetSuggestions);
    
    // Modal
    elements.closeModal.addEventListener('click', closeModal);
    elements.suggestionsModal.addEventListener('click', (e) => {
        if (e.target === elements.suggestionsModal) closeModal();
    });
    
    // Form submission on Enter
    document.querySelectorAll('.task-form input').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleAddTask();
        });
    });
    
    // Set default due date to tomorrow
    elements.taskDue.value = getTodayPlusDays(7);
}

// ============================================
// Input Mode Handling
// ============================================

function handleModeToggle(mode) {
    state.inputMode = mode;
    
    elements.toggleBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    
    elements.formMode.classList.toggle('hidden', mode !== 'form');
    elements.jsonMode.classList.toggle('hidden', mode !== 'json');
}

// ============================================
// Form Handling
// ============================================

function updateImportanceDisplay() {
    elements.importanceDisplay.textContent = elements.taskImportance.value;
}

function handleAddTask() {
    const title = elements.taskTitle.value.trim();
    
    if (!title) {
        showNotification('Please enter a task title', 'error');
        elements.taskTitle.focus();
        return;
    }
    
    const task = {
        id: generateTaskId(),
        title: title,
        due_date: elements.taskDue.value || null,
        estimated_hours: parseFloat(elements.taskHours.value) || 1,
        importance: parseInt(elements.taskImportance.value) || 5,
        dependencies: elements.taskDependencies.value
            ? elements.taskDependencies.value.split(',').map(d => d.trim()).filter(d => d)
            : []
    };
    
    state.tasks.push(task);
    renderTaskList();
    clearForm();
    
    showNotification('Task added successfully', 'success');
}

function clearForm() {
    elements.taskTitle.value = '';
    elements.taskDue.value = getTodayPlusDays(7);
    elements.taskHours.value = '2';
    elements.taskImportance.value = '5';
    elements.importanceDisplay.textContent = '5';
    elements.taskDependencies.value = '';
    elements.taskTitle.focus();
}

function handleClearTasks() {
    if (state.tasks.length === 0) return;
    
    if (confirm('Are you sure you want to clear all tasks?')) {
        state.tasks = [];
        renderTaskList();
        elements.resultsSection.classList.add('hidden');
    }
}

function removeTask(taskId) {
    state.tasks = state.tasks.filter(t => t.id !== taskId);
    renderTaskList();
}

// ============================================
// JSON Handling
// ============================================

function handleLoadSample() {
    elements.jsonInput.value = JSON.stringify(SAMPLE_TASKS, null, 2);
    showNotification('Sample data loaded', 'success');
}

function handleParseJson() {
    const jsonText = elements.jsonInput.value.trim();
    
    if (!jsonText) {
        showNotification('Please enter JSON data', 'error');
        return;
    }
    
    try {
        const parsed = JSON.parse(jsonText);
        
        if (!Array.isArray(parsed)) {
            throw new Error('JSON must be an array of tasks');
        }
        
        // Validate each task has at least a title
        parsed.forEach((task, index) => {
            if (!task.title) {
                throw new Error(`Task at index ${index} is missing a title`);
            }
            // Assign ID if not present
            if (!task.id) {
                task.id = generateTaskId();
            }
        });
        
        state.tasks = parsed;
        renderTaskList();
        handleModeToggle('form');
        
        showNotification(`Successfully loaded ${parsed.length} tasks`, 'success');
    } catch (error) {
        showNotification(`JSON Error: ${error.message}`, 'error');
    }
}

// ============================================
// Task List Rendering
// ============================================

function renderTaskList() {
    elements.taskCount.textContent = state.tasks.length;
    
    if (state.tasks.length === 0) {
        elements.emptyState.classList.remove('hidden');
        elements.taskList.innerHTML = '';
        elements.taskList.appendChild(elements.emptyState);
        return;
    }
    
    elements.emptyState.classList.add('hidden');
    
    const html = state.tasks.map(task => `
        <div class="task-item" data-id="${escapeHtml(task.id)}">
            <div class="task-item-info">
                <div class="task-item-title">${escapeHtml(task.title)}</div>
                <div class="task-item-meta">
                    <span>📅 ${formatDate(task.due_date)}</span>
                    <span>⏱️ ${task.estimated_hours}h</span>
                    <span>⭐ ${task.importance}/10</span>
                    ${task.dependencies && task.dependencies.length > 0 
                        ? `<span>🔗 ${task.dependencies.length} dep(s)</span>` 
                        : ''}
                </div>
            </div>
            <button class="task-item-remove" onclick="removeTask('${escapeHtml(task.id)}')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
    `).join('');
    
    elements.taskList.innerHTML = html;
}

// ============================================
// Strategy Selection
// ============================================

function handleStrategySelect(card) {
    elements.strategyCards.forEach(c => c.classList.remove('active'));
    card.classList.add('active');
    state.currentStrategy = card.dataset.strategy;
}

// ============================================
// API Communication
// ============================================

async function apiRequest(endpoint, method = 'POST', data = null) {
    const url = CONFIG.API_BASE_URL + endpoint;
    
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.details || error.error || 'API request failed');
    }
    
    return response.json();
}

// ============================================
// Analysis
// ============================================

async function handleAnalyze() {
    if (state.tasks.length === 0) {
        showNotification('Please add at least one task to analyze', 'error');
        return;
    }
    
    if (state.isLoading) return;
    
    setLoading(true);
    
    try {
        const result = await apiRequest(CONFIG.ENDPOINTS.ANALYZE, 'POST', {
            tasks: state.tasks,
            strategy: state.currentStrategy
        });
        
        state.lastAnalysisResult = result;
        renderResults(result);
        
        showNotification('Analysis complete!', 'success');
    } catch (error) {
        console.error('Analysis error:', error);
        showNotification(`Analysis failed: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

function setLoading(loading) {
    state.isLoading = loading;
    elements.analyzeBtn.classList.toggle('loading', loading);
    elements.analyzeBtn.disabled = loading;
}

// ============================================
// Results Rendering
// ============================================

function renderResults(result) {
    elements.resultsSection.classList.remove('hidden');
    
    // Meta info
    const strategyNames = {
        smart_balance: 'Smart Balance',
        fastest_wins: 'Fastest Wins',
        high_impact: 'High Impact',
        deadline_driven: 'Deadline Driven'
    };
    elements.resultsMeta.textContent = `${result.total_count} tasks analyzed using ${strategyNames[result.strategy]} strategy`;
    
    // Priority distribution
    const total = result.total_count;
    const dist = result.priority_distribution;
    
    elements.distHigh.style.width = `${(dist.high / total) * 100}%`;
    elements.distMedium.style.width = `${(dist.medium / total) * 100}%`;
    elements.distLow.style.width = `${(dist.low / total) * 100}%`;
    
    elements.countHigh.textContent = dist.high;
    elements.countMedium.textContent = dist.medium;
    elements.countLow.textContent = dist.low;
    
    // Circular dependencies warning
    if (result.circular_dependencies && result.circular_dependencies.length > 0) {
        elements.circularWarning.classList.remove('hidden');
        elements.circularDetails.textContent = `Found ${result.circular_dependencies.length} circular dependency chain(s). Tasks involved may not be completable in sequence.`;
    } else {
        elements.circularWarning.classList.add('hidden');
    }
    
    // Task cards
    elements.resultsGrid.innerHTML = result.tasks.map((task, index) => renderTaskCard(task, index)).join('');
    
    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderTaskCard(task, index) {
    const priorityClass = task.priority_level.toLowerCase();
    const breakdown = task.scoring_breakdown;
    
    return `
        <div class="result-card ${priorityClass}" style="animation-delay: ${index * 0.1}s">
            <div class="result-card-header">
                <div class="result-rank">#${index + 1}</div>
                <div class="result-title-area">
                    <div class="result-title">${escapeHtml(task.title)}</div>
                    ${task.warnings && task.warnings.length > 0 ? `
                        <div class="result-warnings">
                            ${task.warnings.map(w => `<span class="warning-tag">${escapeHtml(w)}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
                <div class="result-score">
                    <span class="score-value">${task.priority_score}</span>
                    <span class="score-label">${task.priority_level}</span>
                </div>
            </div>
            <div class="result-card-body">
                <div class="result-meta">
                    <span class="meta-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                        ${formatDate(task.due_date)}
                    </span>
                    <span class="meta-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12,6 12,12 16,14"/>
                        </svg>
                        ${task.estimated_hours}h effort
                    </span>
                    <span class="meta-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
                        </svg>
                        ${task.importance}/10 importance
                    </span>
                    ${task.dependencies && task.dependencies.length > 0 ? `
                        <span class="meta-item">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/>
                                <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>
                            </svg>
                            ${task.dependencies.length} dependencies
                        </span>
                    ` : ''}
                </div>
                <div class="result-breakdown">
                    <div class="breakdown-title">Score Breakdown</div>
                    <div class="breakdown-grid">
                        <div class="breakdown-item urgency">
                            <div class="breakdown-label">
                                <span>Urgency</span>
                                <span>${breakdown.urgency.weighted_score.toFixed(1)}</span>
                            </div>
                            <div class="breakdown-bar">
                                <div class="breakdown-fill" style="width: ${Math.min(100, breakdown.urgency.score)}%"></div>
                            </div>
                            <div class="breakdown-explanation">${escapeHtml(breakdown.urgency.explanation)}</div>
                        </div>
                        <div class="breakdown-item importance">
                            <div class="breakdown-label">
                                <span>Importance</span>
                                <span>${breakdown.importance.weighted_score.toFixed(1)}</span>
                            </div>
                            <div class="breakdown-bar">
                                <div class="breakdown-fill" style="width: ${breakdown.importance.score}%"></div>
                            </div>
                            <div class="breakdown-explanation">${escapeHtml(breakdown.importance.explanation)}</div>
                        </div>
                        <div class="breakdown-item effort">
                            <div class="breakdown-label">
                                <span>Effort</span>
                                <span>${breakdown.effort.weighted_score.toFixed(1)}</span>
                            </div>
                            <div class="breakdown-bar">
                                <div class="breakdown-fill" style="width: ${breakdown.effort.score}%"></div>
                            </div>
                            <div class="breakdown-explanation">${escapeHtml(breakdown.effort.explanation)}</div>
                        </div>
                        <div class="breakdown-item dependency">
                            <div class="breakdown-label">
                                <span>Dependency</span>
                                <span>${breakdown.dependency.weighted_score.toFixed(1)}</span>
                            </div>
                            <div class="breakdown-bar">
                                <div class="breakdown-fill" style="width: ${breakdown.dependency.score}%"></div>
                            </div>
                            <div class="breakdown-explanation">${escapeHtml(breakdown.dependency.explanation)}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// Suggestions
// ============================================

async function handleGetSuggestions() {
    if (!state.lastAnalysisResult) {
        showNotification('Please analyze tasks first', 'error');
        return;
    }
    
    try {
        const result = await apiRequest(CONFIG.ENDPOINTS.SUGGEST, 'POST', {
            tasks: state.tasks,
            strategy: state.currentStrategy,
            count: 3
        });
        
        renderSuggestions(result);
        openModal();
    } catch (error) {
        console.error('Suggestions error:', error);
        showNotification(`Failed to get suggestions: ${error.message}`, 'error');
    }
}

function renderSuggestions(result) {
    const html = result.suggestions.map(suggestion => `
        <div class="suggestion-card">
            <div class="suggestion-header">
                <div class="suggestion-rank">#${suggestion.rank}</div>
                <div class="suggestion-title">
                    <h3>${escapeHtml(suggestion.task.title)}</h3>
                    <div class="suggestion-score">
                        Priority Score: ${suggestion.task.priority_score} (${suggestion.task.priority_level})
                    </div>
                </div>
            </div>
            <div class="suggestion-reason">
                ${escapeHtml(suggestion.recommendation_reason)}
            </div>
            <div class="suggestion-insight">
                ${escapeHtml(suggestion.actionable_insight)}
            </div>
        </div>
    `).join('');
    
    elements.suggestionsContent.innerHTML = html;
}

// ============================================
// Modal
// ============================================

function openModal() {
    elements.suggestionsModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    elements.suggestionsModal.classList.add('hidden');
    document.body.style.overflow = '';
}

// ============================================
// Notifications
// ============================================

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${escapeHtml(message)}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add styles dynamically if not present
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 10px;
                display: flex;
                align-items: center;
                gap: 1rem;
                z-index: 1000;
                animation: slideInRight 0.3s ease;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }
            .notification button {
                background: none;
                border: none;
                color: inherit;
                font-size: 1.25rem;
                cursor: pointer;
                opacity: 0.7;
            }
            .notification button:hover {
                opacity: 1;
            }
            .notification-success {
                background: rgba(34, 197, 94, 0.9);
                color: white;
            }
            .notification-error {
                background: rgba(239, 68, 68, 0.9);
                color: white;
            }
            .notification-info {
                background: rgba(99, 102, 241, 0.9);
                color: white;
            }
            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(100px); }
                to { opacity: 1; transform: translateX(0); }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => notification.remove(), 300);
        }
    }, 4000);
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    renderTaskList();
    
    // Set initial date
    elements.taskDue.value = getTodayPlusDays(7);
    
    console.log('🚀 Smart Task Analyzer initialized');
});

// Make removeTask available globally for onclick handlers
window.removeTask = removeTask;
