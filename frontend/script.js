document.addEventListener('DOMContentLoaded', () => {
    // Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });

    // Handle Upload Simulation
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadResult = document.getElementById('upload-result');
    const extractedList = document.getElementById('extracted-medicines');

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            simulateUpload();
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            simulateUpload();
        }
    });

    function simulateUpload() {
        uploadArea.innerHTML = '<i class="fa-solid fa-spinner fa-spin upload-icon"></i><p>Extracting medicines...</p>';
        
        setTimeout(() => {
            uploadArea.classList.add('hidden');
            uploadResult.classList.remove('hidden');
            
            const results = [
                { name: 'Paracetamol', purpose: 'Fever relief', time: 'Morning' },
                { name: 'Amoxicillin', purpose: 'Antibiotic', time: 'Afternoon' },
                { name: 'Vitamin D', purpose: 'Bone health', time: 'Night' }
            ];

            extractedList.innerHTML = results.map(item => 
                `<li>
                    <span><strong>${item.name}</strong> - ${item.purpose}</span>
                    <span class="badge-time">${item.time}</span>
                </li>`
            ).join('');
            
            // Allow resetting
            const resetBtn = document.createElement('button');
            resetBtn.className = 'btn-primary';
            resetBtn.style.marginTop = '1rem';
            resetBtn.textContent = 'Upload Another';
            resetBtn.onclick = () => {
                uploadArea.classList.remove('hidden');
                uploadResult.classList.add('hidden');
                uploadArea.innerHTML = '<i class="fa-solid fa-cloud-arrow-up upload-icon"></i><p>Click or drag image to upload and extract medicines</p>';
                fileInput.value = '';
            };
            uploadResult.appendChild(resetBtn);
        }, 1500);
    }

    // Voice Input Simulation
    const voiceBtn = document.getElementById('voice-btn');
    const instructionInput = document.getElementById('instruction-input');

    voiceBtn.addEventListener('click', () => {
        if (voiceBtn.classList.contains('recording')) {
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
        } else {
            voiceBtn.classList.add('recording');
            voiceBtn.innerHTML = '<i class="fa-solid fa-stop"></i>';
            instructionInput.placeholder = "Listening...";
            
            // Simulating speech to text
            setTimeout(() => {
                if (voiceBtn.classList.contains('recording')) {
                    voiceBtn.classList.remove('recording');
                    voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
                    instructionInput.value = "Take Paracetamol in the morning, Amoxicillin in the afternoon, and Vitamin D at night before bed.";
                }
            }, 3000);
        }
    });

    // Generate Schedule Simulation
    const generateBtn = document.getElementById('generate-btn');
    const generatedSchedule = document.getElementById('generated-schedule');
    const morningList = document.getElementById('morning-list');
    const afternoonList = document.getElementById('afternoon-list');
    const nightList = document.getElementById('night-list');
    const scheduleLang = document.getElementById('schedule-lang');

    const scheduleTranslations = {
        en: {
            morning: "Paracetamol (500mg) after breakfast",
            afternoon: "Amoxicillin (250mg) after lunch",
            night: "Vitamin D (1000 IU) before sleep"
        },
        hi: {
            morning: "नाश्ते के बाद पैरासिटामोल (500mg)",
            afternoon: "दोपहर के खाने के बाद अमोक्सिसिलिन (250mg)",
            night: "सोने से पहले विटामिन डी (1000 IU)"
        },
        kn: {
            morning: "ತಿಂಡಿಯ ನಂತರ ಪ್ಯಾರೆಸಿಟಮಾಲ್ (500mg)",
            afternoon: "ಊಟದ ನಂತರ ಅಮಾಕ್ಸಿಸಿಲಿನ್ (250mg)",
            night: "ಮಲಗುವ ಮುನ್ನ ವಿಟಮಿನ್ ಡಿ (1000 IU)"
        }
    };

    generateBtn.addEventListener('click', () => {
        if (!instructionInput.value.trim()) {
            instructionInput.value = "Take Paracetamol in the morning, Amoxicillin in the afternoon, and Vitamin D at night.";
        }

        const lang = scheduleLang.value;
        const routine = scheduleTranslations[lang];

        morningList.innerHTML = `<li>${routine.morning}</li>`;
        afternoonList.innerHTML = `<li>${routine.afternoon}</li>`;
        nightList.innerHTML = `<li>${routine.night}</li>`;

        generatedSchedule.classList.remove('hidden');
    });

    // Intake Tracker Strike-through
    const checkboxes = document.querySelectorAll('.intake-checkbox');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', (e) => {
            const trackerItem = e.target.closest('.tracker-item');
            if (e.target.checked) {
                trackerItem.style.opacity = '0.6';
                trackerItem.querySelector('h4').style.textDecoration = 'line-through';
            } else {
                trackerItem.style.opacity = '1';
                trackerItem.querySelector('h4').style.textDecoration = 'none';
            }
        });
    });

    // Update Date
    const dateSpan = document.getElementById('current-date');
    const today = new Date();
    dateSpan.textContent = today.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
});
