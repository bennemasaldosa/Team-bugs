document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('prescription-form');
    const textarea = document.getElementById('prescription-text');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');
    const errorMsg = document.getElementById('error-message');
    const resultsContainer = document.getElementById('results-container');
    const resetBtn = document.getElementById('reset-btn');

    // Time periods defined from backend expectations
    const periods = ['Morning', 'Afternoon', 'Evening', 'Night'];

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const text = textarea.value.trim();
        if (!text) return;

        // Set Loading state
        btnText.classList.add('hidden');
        spinner.classList.remove('hidden');
        submitBtn.disabled = true;
        errorMsg.classList.add('hidden');
        
        // Hide previous results if any
        resultsContainer.classList.add('hidden');
        
        // Remove animation classes strictly for re-render
        periods.forEach(p => {
            const card = document.getElementById(`card-${p.toLowerCase()}`);
            card.classList.remove('animate-in');
        });

        try {
            const response = await fetch('http://localhost:5000/api/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Failed to parse prescription. Network issue.');
            }

            const rawData = await response.text();
            
            // Try extracting JSON if Gemini wraps it in markdown blocks
            let jsonStr = rawData;
            if (rawData.includes('```json')) {
                jsonStr = rawData.split('```json')[1].split('```')[0].trim();
            } else if (rawData.includes('```')) {
                jsonStr = rawData.split('```')[1].split('```')[0].trim();
            }
            
            const data = JSON.parse(jsonStr);

            // Populate visually
            populateSchedule(data);
            
            // Switch views
            form.classList.add('hidden');
            resultsContainer.classList.remove('hidden');
            
            // Trigger animations
            setTimeout(() => {
                periods.forEach(p => {
                    const card = document.getElementById(`card-${p.toLowerCase()}`);
                    card.classList.add('animate-in');
                });
            }, 50);

        } catch (error) {
            console.error(error);
            errorMsg.textContent = "AI could not process that right now. Please ensure the backend is running & your API key is correct.";
            errorMsg.classList.remove('hidden');
        } finally {
            // Unset loading state
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });

    resetBtn.addEventListener('click', () => {
        textarea.value = '';
        resultsContainer.classList.add('hidden');
        form.classList.remove('hidden');
        textarea.focus();
    });

    function populateSchedule(data) {
        periods.forEach(period => {
            const listId = `list-${period.toLowerCase()}`;
            const listEl = document.getElementById(listId);
            listEl.innerHTML = ''; // Clear existing

            const items = data[period] || [];
            
            if (items.length === 0) {
                const li = document.createElement('li');
                li.className = 'empty-state';
                li.textContent = "No medications scheduled.";
                listEl.appendChild(li);
            } else {
                items.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = item;
                    listEl.appendChild(li);
                });
            }
        });
    }
});
