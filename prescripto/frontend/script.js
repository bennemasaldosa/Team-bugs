document.addEventListener('DOMContentLoaded', () => {
    // Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });

    // Identify current page based on URL to apply correct active state logic
    const currentPath = window.location.pathname;

    // Hide generator if not on dashboard
    const schedulePanel = document.querySelector('.schedule-panel');
    if (schedulePanel) schedulePanel.style.display = 'none';


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

        const btnOriginalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';

        fetch('/generate_schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instructions: instructionInput.value })
        })
            .then(response => response.json())
            .then(data => {
                const formatList = (arr) => arr && arr.length > 0 ? arr.map(item => `<li>${item}</li>`).join('') : '<li style="color:#94a3b8;">None</li>';

                morningList.innerHTML = formatList(data.morning);
                afternoonList.innerHTML = formatList(data.afternoon || []);
                nightList.innerHTML = formatList(data.night || []);

                generatedSchedule.classList.remove('hidden');
                generateBtn.innerHTML = btnOriginalText;
            })
            .catch(err => {
                console.error(err);
                generateBtn.innerHTML = btnOriginalText;

                // Fallback to translations if backend is unavailable
                const lang = scheduleLang.value;
                const routine = scheduleTranslations[lang] || scheduleTranslations['en'];
                morningList.innerHTML = `<li>${routine.morning}</li>`;
                afternoonList.innerHTML = `<li>${routine.afternoon}</li>`;
                nightList.innerHTML = `<li>${routine.night}</li>`;
                generatedSchedule.classList.remove('hidden');
            });
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

    // Search Bar filtering
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();

            // Filter History Table
            const rows = document.querySelectorAll('.medicine-table tbody tr');
            rows.forEach(row => {
                const medName = row.querySelector('td:first-child').textContent.toLowerCase();
                const desc = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                if (medName.includes(query) || desc.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });

            // Filter Intake Tracker
            const trackerItems = document.querySelectorAll('.tracker-item');
            trackerItems.forEach(item => {
                const itemName = item.querySelector('h4').textContent.toLowerCase();
                const itemDesc = item.querySelector('p').textContent.toLowerCase();
                if (itemName.includes(query) || itemDesc.includes(query)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // Sidebar Active State handling (Now just closes the menu on mobile)
    const navLinks = document.querySelectorAll('.nav-links li');
    navLinks.forEach(item => {
        item.addEventListener('click', (e) => {
            // On mobile, close sidebar after clicking a link
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
            }
        });
    });

    // Global Language syncing
    const globalLang = document.getElementById('global-lang');
    if (globalLang) {
        globalLang.addEventListener('change', (e) => {
            if (scheduleLang) {
                scheduleLang.value = e.target.value;
            }
        });
    }


    /* --- Customer Support Logic --- */


    /* --- Redesigned Customer Support Logic --- */

    // 1. FAQ Search Filtering Logic (Updated for Cards)
    const helpSearch = document.getElementById('help-search');
    const faqCards = document.querySelectorAll('.faq-card');
    const emptyState = document.getElementById('no-results');

    if (helpSearch) {
        helpSearch.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            let hasMatches = false;

            faqCards.forEach(card => {
                const headText = card.querySelector('.faq-header h4').textContent.toLowerCase();
                const bodyText = card.querySelector('.faq-body p').textContent.toLowerCase();

                if (headText.includes(term) || bodyText.includes(term)) {
                    card.style.display = 'block';
                    hasMatches = true;
                } else {
                    card.style.display = 'none';
                }
            });

            // Toggle "Empty state" message
            if (emptyState) {
                emptyState.style.display = (hasMatches || term === "") ? 'none' : 'block';
            }
        });
    }

    // 2. FAQ Accordion Behavior (Updated for Cards)
    faqCards.forEach(card => {
        const header = card.querySelector('.faq-header');
        header.addEventListener('click', () => {
            const isActive = card.classList.contains('active');
            
            // Close all other card items
            faqCards.forEach(c => {
                if (c !== card) c.classList.remove('active');
            });
            
            // Toggle clicked card
            card.classList.toggle('active');
        });
    });

    // 3. Quick Help Tag Navigation
    const suggestionTags = document.querySelectorAll('.suggestion-tag');
    suggestionTags.forEach(tag => {
        tag.addEventListener('click', () => {
            const targetId = tag.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Focus search with tag text
                if (helpSearch) helpSearch.value = tag.textContent;
                
                // Scroll to target
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Open the target card
                faqCards.forEach(c => c.classList.remove('active'));
                targetElement.classList.add('active');
            }
        });
    });

    // 4. Enhanced Support Form Validation
    const supportForm = document.getElementById('support-form');
    if (supportForm) {
        supportForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const nameField = document.getElementById('support-name');
            const emailField = document.getElementById('support-email');
            const issueField = document.getElementById('issue-type');
            const messageField = document.getElementById('support-message');
            
            let isValid = true;

            const setError = (id, msg) => {
                const errorSpan = document.getElementById(id);
                const input = errorSpan.previousElementSibling;
                if (msg) {
                    errorSpan.textContent = msg;
                    input.classList.add('invalid');
                    isValid = false;
                } else {
                    errorSpan.textContent = "";
                    input.classList.remove('invalid');
                }
            };

            // Validations
            if (nameField.value.trim() === "") setError('name-error', "Please enter your full name");
            else setError('name-error', "");

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailField.value.trim())) setError('email-error', "Enter a valid email address");
            else setError('email-error', "");

            if (issueField.value === "") setError('issue-error', "Please select a topic");
            else setError('issue-error', "");

            if (messageField.value.trim().length < 10) setError('message-error', "Message must be at least 10 characters");
            else setError('message-error', "");

            if (isValid) {
                const btn = supportForm.querySelector('button');
                const originalText = btn.textContent;
                btn.disabled = true;
                btn.textContent = "Submitting...";

                setTimeout(() => {
                    alert("Thank you! Your support request has been submitted successfully. Our team will contact you within 24 hours.");
                    btn.disabled = false;
                    btn.textContent = originalText;
                    supportForm.reset();
                    // Clear error states
                    document.querySelectorAll('.error-msg').forEach(s => s.textContent = "");
                    document.querySelectorAll('.invalid').forEach(i => i.classList.remove('invalid'));
                }, 1500);
            }
        });
    }

    /* --- Manual Auth Logic (Login/Register) --- */
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const loginSection = document.getElementById('login-section');
    const registerSection = document.getElementById('register-section');
    const authMessage = document.getElementById('auth-message');

    if (tabLogin && tabRegister) {
        // Initial check for Google Client ID
        const googleIdTag = document.getElementById('g_id_onload');
        const googleStatus = document.getElementById('google-signin-status');
        if (googleIdTag && googleIdTag.getAttribute('data-client_id').includes('your_google_client_id')) {
            console.warn("Prescripto: Google Client ID is not configured. Enabling Simulation Mode.");
            if (googleStatus) googleStatus.style.display = 'block';
            // Hide the real button if unconfigured
            const realGoogleBtn = document.querySelector('.g_id_signin');
            if (realGoogleBtn) realGoogleBtn.style.display = 'none';
        }

        tabLogin.addEventListener('click', () => {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            loginSection.style.display = 'block';
            registerSection.style.display = 'none';
            authMessage.style.display = 'none';
        });

        tabRegister.addEventListener('click', () => {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            registerSection.style.display = 'block';
            loginSection.style.display = 'none';
            authMessage.style.display = 'none';
        });
    }

    const showAuthMessage = (msg, isError = true) => {
        if (!authMessage) return;
        authMessage.innerText = msg;
        authMessage.style.display = 'block';
        authMessage.style.background = isError ? '#fef2f2' : '#ecfdf5';
        authMessage.style.color = isError ? '#dc2626' : '#059669';
    };

    // Manual Login Form
    const manualLoginForm = document.getElementById('manual-login-form');
    if (manualLoginForm) {
        manualLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    window.location.href = data.redirect;
                } else {
                    showAuthMessage(data.message);
                }
            } catch (err) {
                console.error('Manual Login Error:', err);
                showAuthMessage('Connection error. Please check if the backend is running.');
            }
        });
    }

    // Registration Form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    showAuthMessage('Registration successful! Please login.', false);
                    setTimeout(() => tabLogin.click(), 1500);
                } else {
                    showAuthMessage(data.message);
                }
            } catch (err) {
                console.error('Registration Error:', err);
                showAuthMessage('Connection error. Please try again later.');
            }
        });
    }

    /* --- Profile Dropdown & Session Logic --- */
    const userProfile = document.querySelector('.user-profile');
    const topNav = document.querySelector('.top-nav');

    if (userProfile && topNav) {
        // Create dropdown element dynamically if it doesn't exist
        let dropdown = document.querySelector('.profile-dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.className = 'profile-dropdown';
            dropdown.innerHTML = `
                <div class="dropdown-user-info">
                    <img src="" alt="Avatar" class="avatar-large">
                    <h4>User Name</h4>
                    <p>user@example.com</p>
                </div>
                <div class="dropdown-links">
                    <a href="/profile"><i class="fa-regular fa-user"></i> My Profile</a>
                    <a href="/settings"><i class="fa-solid fa-gear"></i> Settings</a>
                    <a href="/logout" class="logout-btn"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
                </div>
            `;
            userProfile.appendChild(dropdown);
        }

        userProfile.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('active');
        });

        document.addEventListener('click', () => {
            dropdown.classList.remove('active');
        });

        dropdown.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Fetch User Info
        fetch('/api/user-info')
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const user = data.user;
                    // Update Top Nav Avatar
                    const navAvatar = userProfile.querySelector('.avatar');
                    if (navAvatar && user.picture) navAvatar.src = user.picture;

                    // Update Dropdown Info
                    const dropAvatar = dropdown.querySelector('.avatar-large');
                    const dropName = dropdown.querySelector('h4');
                    const dropEmail = dropdown.querySelector('p');

                    if (dropAvatar && user.picture) dropAvatar.src = user.picture;
                    if (dropName) dropName.textContent = user.name;
                    if (dropEmail) dropEmail.textContent = user.email;
                }
            })
            .catch(err => console.error('Error fetching user info:', err));
    }

    /* --- Demo & Simulation Helpers --- */
    window.simulateGoogleLogin = async () => {
        showAuthMessage('Simulating Google Auth...', false);
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: "demo.user@gmail.com", password: "demo_password", is_demo: true })
            });
            const data = await response.json();
            if (data.status === 'success') window.location.href = data.redirect;
        } catch (err) {
            window.location.href = '/dashboard';
        }
    };

    window.useDemoAccount = () => {
        const emailInput = document.getElementById('login-email');
        const passInput = document.getElementById('login-password');
        if (emailInput && passInput) {
            emailInput.value = "demo.user@gmail.com";
            passInput.value = "demo_password";
            const loginForm = document.getElementById('manual-login-form');
            if (loginForm) loginForm.dispatchEvent(new Event('submit'));
        }
    };
});

