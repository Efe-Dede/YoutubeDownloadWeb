/**
 * Video Downloader - Frontend Application
 */

// API Base URL and Key
const API_BASE = '/api';
const API_KEY = '[[API_KEY_PLACEHOLDER]]';

// State
let currentVideoData = null;
let currentJobId = null;
let progressInterval = null;

// DOM Elements
const elements = {
    urlInput: document.getElementById('urlInput'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    videoCard: document.getElementById('videoCard'),
    thumbnail: document.getElementById('thumbnail'),
    duration: document.getElementById('duration'),
    videoTitle: document.getElementById('videoTitle'),
    uploader: document.getElementById('uploader'),
    qualitySelect: document.getElementById('qualitySelect'),
    downloadBtn: document.getElementById('downloadBtn'),
    progressSection: document.getElementById('progressSection'),
    progressPercent: document.getElementById('progressPercent'),
    progressFill: document.getElementById('progressFill'),
    progressSpeed: document.getElementById('progressSpeed'),
    progressEta: document.getElementById('progressEta'),
    completeSection: document.getElementById('completeSection'),
    downloadFilename: document.getElementById('downloadFilename'),
    downloadLink: document.getElementById('downloadLink'),
    newDownloadBtn: document.getElementById('newDownloadBtn'),
    errorSection: document.getElementById('errorSection'),
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn')
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    // Event listeners
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAnalyze();
    });
    elements.downloadBtn.addEventListener('click', handleDownload);
    elements.newDownloadBtn.addEventListener('click', resetApp);
    elements.retryBtn.addEventListener('click', resetApp);
}

// Analyze video
async function handleAnalyze() {
    const url = elements.urlInput.value.trim();

    if (!url) {
        showError('Lütfen bir video URL\'si girin');
        return;
    }

    setLoading(true);
    hideAllSections();

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.success) {
            currentVideoData = data;
            displayVideoInfo(data);
        } else {
            showError(data.error || 'Video analiz edilemedi');
        }
    } catch (error) {
        showError('Bağlantı hatası: ' + error.message);
    } finally {
        setLoading(false);
    }
}

// Display video information
function displayVideoInfo(data) {
    elements.thumbnail.src = data.thumbnail || '';
    elements.thumbnail.alt = data.title || 'Video Thumbnail';
    elements.duration.textContent = data.duration_string || '00:00';
    elements.videoTitle.textContent = data.title || 'Bilinmeyen Video';
    elements.uploader.textContent = data.uploader || 'Bilinmeyen Kanal';

    // Populate quality options from API response
    if (data.formats && data.formats.length > 0) {
        populateQualityOptions(data.formats);
    }

    elements.videoCard.classList.remove('hidden');
}

// Populate quality dropdown
function populateQualityOptions(formats) {
    // Keep default options
    const defaultOptions = `
        <option value="best">En İyi Kalite</option>
        <option value="1080p">1080p (Full HD)</option>
        <option value="720p">720p (HD)</option>
        <option value="480p">480p</option>
        <option value="360p">360p</option>
        <option value="audio">Sadece Ses (MP3)</option>
    `;
    elements.qualitySelect.innerHTML = defaultOptions;
}

// Start download
async function handleDownload() {
    const url = (currentVideoData && currentVideoData.webpage_url)
        ? currentVideoData.webpage_url
        : elements.urlInput.value.trim();
    const quality = elements.qualitySelect.value;

    const requestBody = {
        url,
        quality,
        start_time: null,
        end_time: null
    };

    hideAllSections();
    elements.progressSection.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.success && data.job_id) {
            currentJobId = data.job_id;
            startProgressPolling();
        } else {
            showError(data.error || 'İndirme başlatılamadı');
        }
    } catch (error) {
        showError('Bağlantı hatası: ' + error.message);
    }
}

// Start polling for progress
function startProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }

    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/progress/${currentJobId}`, {
                headers: {
                    'X-API-Key': API_KEY
                }
            });
            const data = await response.json();

            updateProgress(data);

            if (data.status === 'completed') {
                stopProgressPolling();
                showComplete(data);
            } else if (data.status === 'failed') {
                stopProgressPolling();
                showError(data.error || 'İndirme başarısız oldu');
            }
        } catch (error) {
            console.error('Progress check error:', error);
        }
    }, 500);
}

// Stop progress polling
function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

// Update progress UI
function updateProgress(data) {
    const progress = Math.round(data.progress || 0);
    elements.progressPercent.textContent = `${progress}%`;
    elements.progressFill.style.width = `${progress}%`;
    elements.progressSpeed.textContent = data.speed || '-- MB/s';
    elements.progressEta.textContent = data.eta ? `Kalan: ${data.eta}` : 'Kalan: --';
}

// Show complete UI
function showComplete(data) {
    hideAllSections();

    const filename = data.filename || 'video.mp4';
    elements.downloadFilename.textContent = filename;

    // Direct link doesn't support headers, so we handle download via fetch
    elements.downloadLink.onclick = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${API_BASE}/file/${currentJobId}`, {
                headers: { 'X-API-Key': API_KEY }
            });
            if (!response.ok) throw new Error('İndirme başarısız');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            showError('Dosya indirilirken hata oluştu');
        }
    };

    elements.completeSection.classList.remove('hidden');
}

// Show error
function showError(message) {
    hideAllSections();
    elements.errorMessage.textContent = message;
    elements.errorSection.classList.remove('hidden');
}

// Hide all sections
function hideAllSections() {
    elements.videoCard.classList.add('hidden');
    elements.progressSection.classList.add('hidden');
    elements.completeSection.classList.add('hidden');
    elements.errorSection.classList.add('hidden');
}

// Reset app
function resetApp() {
    stopProgressPolling();
    currentVideoData = null;
    currentJobId = null;

    elements.urlInput.value = '';
    elements.progressFill.style.width = '0%';
    elements.progressPercent.textContent = '0%';

    hideAllSections();
}

// Set loading state
function setLoading(loading) {
    const btnText = elements.analyzeBtn.querySelector('.btn-text');
    const btnLoader = elements.analyzeBtn.querySelector('.btn-loader');

    if (loading) {
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        elements.analyzeBtn.disabled = true;
    } else {
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        elements.analyzeBtn.disabled = false;
    }
}
