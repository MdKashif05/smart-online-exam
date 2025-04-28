document.addEventListener('DOMContentLoaded', function() {
    // Question type handling
    const questionTypeSelect = document.getElementById('question_type');
    const optionsContainer = document.getElementById('options-container');
    
    if (questionTypeSelect && optionsContainer) {
        // Initial state
        updateOptionsVisibility();
        
        // Update on change
        questionTypeSelect.addEventListener('change', updateOptionsVisibility);
        
        function updateOptionsVisibility() {
            if (questionTypeSelect.value === 'single_choice' || questionTypeSelect.value === 'multiple_choice') {
                optionsContainer.style.display = 'block';
                
                // Update the correct option input type based on question type
                const correctOptionInputs = document.querySelectorAll('.correct-option');
                correctOptionInputs.forEach(input => {
                    if (questionTypeSelect.value === 'single_choice') {
                        input.type = 'radio';
                    } else {
                        input.type = 'checkbox';
                    }
                });
            } else {
                optionsContainer.style.display = 'none';
            }
        }
    }
    
    // Add more options button
    const addOptionBtn = document.getElementById('add-option-btn');
    if (addOptionBtn) {
        addOptionBtn.addEventListener('click', function() {
            const optionsContainer = document.getElementById('options-list');
            const optionsCount = optionsContainer.querySelectorAll('.option-item').length;
            const newOptionHtml = `
                <div class="option-item mb-2 row align-items-center">
                    <div class="col-1">
                        <input type="${questionTypeSelect.value === 'single_choice' ? 'radio' : 'checkbox'}" 
                            name="correct_options[]" 
                            value="${optionsCount}" 
                            class="correct-option form-check-input">
                    </div>
                    <div class="col-10">
                        <input type="text" name="options[]" class="form-control" placeholder="Option text">
                    </div>
                    <div class="col-1">
                        <button type="button" class="btn btn-sm btn-danger remove-option">✕</button>
                    </div>
                </div>
            `;
            
            // Insert new option
            optionsContainer.insertAdjacentHTML('beforeend', newOptionHtml);
            
            // Add event listener to remove button
            const removeBtn = optionsContainer.querySelector('.option-item:last-child .remove-option');
            removeBtn.addEventListener('click', function() {
                this.closest('.option-item').remove();
            });
        });
    }
    
    // Remove option buttons (for existing buttons)
    document.querySelectorAll('.remove-option').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.option-item').remove();
        });
    });
    
    // Confirm delete operations
    document.querySelectorAll('.confirm-delete').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // User management - search functionality
    const userSearchInput = document.getElementById('user-search');
    if (userSearchInput) {
        userSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('#users-table tbody tr').forEach(row => {
                const username = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
                const email = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                
                if (username.includes(searchTerm) || email.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Exam management - search functionality
    const examSearchInput = document.getElementById('exam-search');
    if (examSearchInput) {
        examSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('#exams-table tbody tr').forEach(row => {
                const title = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
                const description = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Statistics Charts
    const userStatsCanvas = document.getElementById('user-stats-chart');
    if (userStatsCanvas) {
        fetch('/admin/api/user-stats')
            .then(response => response.json())
            .then(data => {
                const ctx = userStatsCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'New Users',
                            data: data.values,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            tension: 0.1,
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error fetching user stats:', error));
    }
    
    const examStatsCanvas = document.getElementById('exam-stats-chart');
    if (examStatsCanvas) {
        fetch('/admin/api/exam-stats')
            .then(response => response.json())
            .then(data => {
                const ctx = examStatsCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Exams Taken',
                            data: data.values,
                            backgroundColor: 'rgba(153, 102, 255, 0.6)',
                            borderColor: 'rgba(153, 102, 255, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error fetching exam stats:', error));
    }
});
