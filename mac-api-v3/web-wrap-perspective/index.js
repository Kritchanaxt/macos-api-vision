// Tab functionality
const tabs = document.querySelectorAll('.tab');
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const targetId = tab.getAttribute('data-target');
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(targetId).classList.add('active');
    });
});

const uploadButton = document.getElementById('uploadButton');
const detectButton = document.getElementById('detectButton');
const imageFile = document.getElementById('imageFile');
const uploadedImage = document.getElementById('uploadedImage');
const imageContainer = document.getElementById('imageContainer');
const dimensionsRow = document.getElementById('dimensionsRow');
const outputWidth = document.getElementById('outputWidth');
const outputHeight = document.getElementById('outputHeight');
const correctButton = document.getElementById('correctButton');
const resetButton = document.getElementById('resetButton');
const loading = document.getElementById('loading');
const resultContainer = document.getElementById('resultContainer');
const resultImage = document.getElementById('resultImage');
const resultInfo = document.getElementById('resultInfo');
const errorMessage = document.getElementById('errorMessage');

// Define the API base URL - update this to match your backend
const API_BASE_URL = 'http://localhost:8000';

let imageSrc = "";
let imageBlob = null;
let points = [
    { id: 'point1', x: 0.1, y: 0.1 },
    { id: 'point2', x: 0.9, y: 0.1 },
    { id: 'point3', x: 0.9, y: 0.9 },
    { id: 'point4', x: 0.1, y: 0.9 }
];

// Function to show error
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

// Function to hide error
function hideError() {
    errorMessage.classList.add('hidden');
}

// Function to upload image
uploadButton.addEventListener('click', () => {
    const file = imageFile.files[0];
    if (file) {
        imageBlob = file;
        const reader = new FileReader();
        reader.onload = function(e) {
            imageSrc = e.target.result;
            uploadedImage.src = imageSrc;
            imageContainer.classList.remove('hidden');
            dimensionsRow.classList.remove('hidden');
            correctButton.disabled = false;
            detectButton.classList.remove('hidden');
            resetButton.classList.remove('hidden');
            hideError();
            resultContainer.classList.add('hidden');
        };
        reader.readAsDataURL(file);
    }
});

// Function to detect rectangle
detectButton.addEventListener('click', async () => {
    if (!imageBlob) {
        showError('กรุณาอัปโหลดรูปภาพก่อน');
        return;
    }
    
    detectButton.disabled = true;
    loading.classList.remove('hidden');
    
    try {
        const formData = new FormData();
        formData.append('file', imageBlob);
        
        const response = await fetch(`${API_BASE_URL}/perspective/detect-rectangle`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('ไม่สามารถตรวจจับขอบได้');
        }
        
        const data = await response.json();
        
        if (data.points && data.points.length === 4) {
            // Update points based on API response
            const imgWidth = uploadedImage.width;
            const imgHeight = uploadedImage.height;
            
            data.points.forEach((point, index) => {
                points[index].x = point.x / imgWidth;
                points[index].y = point.y / imgHeight;
                
                const element = document.getElementById(points[index].id);
                element.style.left = `${points[index].x * 100}%`;
                element.style.top = `${points[index].y * 100}%`;
            });
            
            updateLines();
        }
    } catch (error) {
        showError(error.message);
    } finally {
        loading.classList.add('hidden');
        detectButton.disabled = false;
    }
});

// Function to reset the points
resetButton.addEventListener('click', () => {
    points = [
        { id: 'point1', x: 0.1, y: 0.1 },
        { id: 'point2', x: 0.9, y: 0.1 },
        { id: 'point3', x: 0.9, y: 0.9 },
        { id: 'point4', x: 0.1, y: 0.9 }
    ];
    
    points.forEach((point) => {
        const element = document.getElementById(point.id);
        element.style.top = `${point.y * 100}%`;
        element.style.left = `${point.x * 100}%`;
    });
    
    updateLines();
    hideError();
});

// Drag functionality for points
points.forEach(point => {
    const element = document.getElementById(point.id);
    let isDragging = false;
    
    // For mouse events
    element.addEventListener('mousedown', (e) => {
        e.preventDefault();
        startDrag(e, element, point);
    });
    
    // For touch events
    element.addEventListener('touchstart', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        startDrag(touch, element, point);
    });
    
    function startDrag(e, element, point) {
        isDragging = true;
        const rect = element.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        const offsetY = e.clientY - rect.top;
        
        // For mouse move
        const onMouseMove = (e) => {
            if (isDragging) {
                movePoint(e, offsetX, offsetY, point, element);
            }
        };
        
        // For touch move
        const onTouchMove = (e) => {
            if (isDragging) {
                e.preventDefault();
                const touch = e.touches[0];
                movePoint(touch, offsetX, offsetY, point, element);
            }
        };
        
        // End drag function
        const endDrag = () => {
            isDragging = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', endDrag);
            document.removeEventListener('touchmove', onTouchMove);
            document.removeEventListener('touchend', endDrag);
        };
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchmove', onTouchMove, { passive: false });
        document.addEventListener('touchend', endDrag);
    }
    
    function movePoint(e, offsetX, offsetY, point, element) {
        const imgRect = imageContainer.getBoundingClientRect();
        const imgWidth = uploadedImage.clientWidth;
        const imgHeight = uploadedImage.clientHeight;
        
        // Calculate the position relative to the image
        const imgOffsetX = (uploadedImage.clientWidth - imgWidth) / 2;
        const imgOffsetY = (uploadedImage.clientHeight - imgHeight) / 2;
        
        let x = (e.clientX - imgRect.left - offsetX) / imgWidth;
        let y = (e.clientY - imgRect.top - offsetY) / imgHeight;
        
        // Constrain to image boundaries
        x = Math.max(0, Math.min(1, x));
        y = Math.max(0, Math.min(1, y));
        
        point.x = x;
        point.y = y;
        element.style.left = `${x * 100}%`;
        element.style.top = `${y * 100}%`;
        updateLines();
    }
});

// Update the lines based on the points
function updateLines() {
    for (let i = 0; i < 4; i++) {
        const currentPoint = points[i];
        const nextPoint = points[(i + 1) % 4];
        
        const line = document.getElementById(`line${i + 1}`);
        const x1 = currentPoint.x * 100;
        const y1 = currentPoint.y * 100;
        const x2 = nextPoint.x * 100;
        const y2 = nextPoint.y * 100;
        
        const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
        const angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI);
        
        line.style.width = `${length}%`;
        line.style.height = '2px';
        line.style.transformOrigin = '0 0';
        line.style.transform = `rotate(${angle}deg)`;
        line.style.top = `${y1}%`;
        line.style.left = `${x1}%`;
    }
}

// Function to correct the perspective
correctButton.addEventListener('click', async () => {
    if (!imageBlob) {
        showError('กรุณาอัปโหลดรูปภาพก่อน');
        return;
    }
    
    correctButton.disabled = true;
    loading.classList.remove('hidden');
    hideError();
    
    try {
        // Create FormData
        const formData = new FormData();
        formData.append('file', imageBlob);
        
        // Convert relative coordinates to actual image coordinates
        const imgWidth = uploadedImage.naturalWidth;
        const imgHeight = uploadedImage.naturalHeight;
        
        const pointsData = points.map(point => ({
            x: point.x * imgWidth,
            y: point.y * imgHeight
        }));
        
        formData.append('points', JSON.stringify(pointsData));
        
        // Add optional output dimensions if specified
        if (outputWidth.value) formData.append('output_width', outputWidth.value);
        if (outputHeight.value) formData.append('output_height', outputHeight.value);
        
        // Send the API request
        const response = await fetch(`${API_BASE_URL}/perspective`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'การปรับภาพล้มเหลว');
        }
        
        const data = await response.json();
        
        // Build the full URL for the result image
        const resultImageUrl = new URL(data.output_path, API_BASE_URL).href;
        
        // Display the result
        resultImage.src = resultImageUrl;
        resultContainer.classList.remove('hidden');
        
        // Display info about the processed image
        resultInfo.innerHTML = `
            <p><strong>ขนาด:</strong> ${data.width} x ${data.height} พิกเซล</p>
            <p><strong>อัตราเร่ง:</strong> ${data.fast_rate.toFixed(2)}</p>
            <p><strong>อัตราระบายความร้อน:</strong> ${data.rack_cooling_rate.toFixed(2)}</p>
        `;
    } catch (error) {
        showError(error.message);
    } finally {
        loading.classList.add('hidden');
        correctButton.disabled = false;
    }
});

// Initialize lines on page load
updateLines();