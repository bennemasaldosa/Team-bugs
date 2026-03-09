// Main Interactive Logic for Prescripto
document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const instructionsInput = document.getElementById('instructions');
    const scheduleSection = document.querySelector('.schedule-section');
    
    // UI lists elements wrapper object
    const lists = {
        morning: document.getElementById('morning-list'),
        afternoon: document.getElementById('afternoon-list'),
        evening: document.getElementById('evening-list'),
        night: document.getElementById('night-list')
    };

    generateBtn.addEventListener('click', async () => {
        const text = instructionsInput.value.trim();
        
        // Prevent empty submissions
        if (!text) {
            alert('Please enter some prescription instructions before generating a schedule.');
            return;
        }

        // Add loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = 'Generating... ⏳';

        try {
            // Send the instruction text to the backend API via POST request
            const response = await fetch('/generate_schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ instructions: text })
            });

            if (!response.ok) {
                throw new Error(`Server errror: ${response.status}`);
            }

            // Parse the JSON response block
            const data = await response.json();
            
            // Render the results into the UI
            renderSchedule(data);
            
            // Show the schedule section with CSS animation
            scheduleSection.style.display = 'block';
            
            // Smoothly scroll down to show the results
            scheduleSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
        } catch (error) {
            console.error('Error generating schedule:', error);
            alert('An error occurred while communicating with the backend. Ensure the Flask server is running.');
        } finally {
            // Reset loading state
            generateBtn.disabled = false;
            generateBtn.innerHTML = 'Generate Schedule';
        }
    });

    /**
     * Renders parsed medicine data into corresponding time cards
     * Expected data format: { morning: ["Med1"], afternoon: [], evening: [], night: [] }
     */
    function renderSchedule(data) {
        for (const [timeOfDay, medicines] of Object.entries(data)) {
            const listElement = lists[timeOfDay];
            if (!listElement) continue; // Skip unknown slots
            
            // Clean up the pre-existing contents
            listElement.innerHTML = '';
            
            if (medicines && medicines.length > 0) {
                // Remove duplicates by using Set properly or assume the backend handle it
                // For this simplistic model, we'll just display everything 
                medicines.forEach(med => {
                    const li = document.createElement('li');
                    li.textContent = med;
                    listElement.appendChild(li);
                });
            } else {
                // Create informative empty message gracefully
                const emptyMsg = document.createElement('div');
                emptyMsg.className = 'empty-message';
                emptyMsg.textContent = 'No medicines scheduled';
                listElement.appendChild(emptyMsg);
            }
        }
    }
});
