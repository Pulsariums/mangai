// Theme Management
const themeToggle = document.getElementById('themeToggle');
const htmlElement = document.documentElement;

// Load saved theme or default to light mode
const savedTheme = localStorage.getItem('theme') || 'light';
htmlElement.setAttribute('data-theme', savedTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
});

// File Upload Handling
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const imageGrid = document.getElementById('imageGrid');
const emptyState = document.getElementById('emptyState');
const processBtn = document.getElementById('processBtn');
const exportBtn = document.getElementById('exportBtn');

let uploadedImages = [];

// Click to upload
dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

// Drag and drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
    const imageFiles = Array.from(files).filter(file => 
        file.type.startsWith('image/')
    );

    if (imageFiles.length === 0) return;

    emptyState.style.display = 'none';
    
    imageFiles.forEach(file => {
        const id = Date.now() + Math.random().toString(36).substr(2, 9);
        const reader = new FileReader();
        
        reader.onload = (e) => {
            uploadedImages.push({
                id,
                name: file.name,
                size: file.size,
                type: file.type,
                dataUrl: e.target.result,
                status: 'pending'
            });
            
            renderImageCard(uploadedImages[uploadedImages.length - 1]);
            updateButtonStates();
        };
        
        reader.readAsDataURL(file);
    });
}

function renderImageCard(imageData) {
    const card = document.createElement('div');
    card.className = 'image-card';
    card.dataset.id = imageData.id;
    
    card.innerHTML = `
        <img src="${imageData.dataUrl}" alt="${imageData.name}">
        <div class="image-card-info">
            <div class="image-card-name">${imageData.name}</div>
            <div class="image-card-status">${formatFileSize(imageData.size)}</div>
        </div>
        <div class="image-card-actions">
            <button class="action-btn" title="Remove" onclick="removeImage('${imageData.id}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </div>
    `;
    
    imageGrid.appendChild(card);
}

function removeImage(id) {
    uploadedImages = uploadedImages.filter(img => img.id !== id);
    const card = document.querySelector(`.image-card[data-id="${id}"]`);
    if (card) {
        card.remove();
    }
    
    if (uploadedImages.length === 0) {
        emptyState.style.display = 'flex';
    }
    
    updateButtonStates();
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function updateButtonStates() {
    const hasImages = uploadedImages.length > 0;
    processBtn.disabled = !hasImages;
    exportBtn.disabled = !hasImages;
}

// Process Button
processBtn.addEventListener('click', async () => {
    const apiKey = document.getElementById('apiKey').value;
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;
    const autoInpaint = document.getElementById('autoInpaint').checked;
    const preserveStyle = document.getElementById('preserveStyle').checked;

    if (!apiKey) {
        alert('Please enter your Gemini API key');
        return;
    }

    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    progressContainer.style.display = 'flex';
    
    // Simulate processing (in real app, this would call Rust backend)
    for (let i = 0; i < uploadedImages.length; i++) {
        const image = uploadedImages[i];
        image.status = 'processing';
        updateImageStatus(image.id, 'processing');
        
        progressText.textContent = `Processing ${i + 1}/${uploadedImages.length}: ${image.name}`;
        progressFill.style.width = `${((i + 1) / uploadedImages.length) * 100}%`;
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        image.status = 'completed';
        updateImageStatus(image.id, 'completed');
    }
    
    progressText.textContent = 'Completed!';
    
    setTimeout(() => {
        progressContainer.style.display = 'none';
        progressFill.style.width = '0%';
    }, 2000);
});

function updateImageStatus(id, status) {
    const card = document.querySelector(`.image-card[data-id="${id}"]`);
    if (!card) return;
    
    const statusEl = card.querySelector('.image-card-status');
    if (status === 'processing') {
        statusEl.textContent = 'Processing...';
        statusEl.style.color = 'var(--warning)';
    } else if (status === 'completed') {
        statusEl.textContent = '✓ Completed';
        statusEl.style.color = 'var(--success)';
    }
}

// Export Button
exportBtn.addEventListener('click', () => {
    // In real app, this would export results from Rust backend
    alert('Export functionality will be implemented in the Rust backend');
});

// Tauri integration (when running as desktop/mobile app)
if (window.__TAURI__) {
    const { invoke } = window.__TAURI__.core;
    
    // Override process function to call Rust backend
    processBtn.addEventListener('click', async () => {
        const apiKey = document.getElementById('apiKey').value;
        const sourceLang = document.getElementById('sourceLang').value;
        const targetLang = document.getElementById('targetLang').value;
        const autoInpaint = document.getElementById('autoInpaint').checked;
        const preserveStyle = document.getElementById('preserveStyle').checked;

        if (!apiKey) {
            alert('Please enter your Gemini API key');
            return;
        }

        try {
            const result = await invoke('process_images', {
                images: uploadedImages.map(img => ({
                    id: img.id,
                    name: img.name,
                    data: img.dataUrl
                })),
                config: {
                    sourceLang,
                    targetLang,
                    autoInpaint,
                    preserveStyle,
                    apiKey
                }
            });
            
            console.log('Processing result:', result);
        } catch (error) {
            console.error('Error processing images:', error);
            alert('Error processing images: ' + error);
        }
    });
}

console.log('Manga Translator UI initialized');
