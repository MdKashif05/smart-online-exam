document.addEventListener('DOMContentLoaded', function() {
    // Variables for exam state
    const examForm = document.getElementById('exam-form');
    const timerElement = document.getElementById('timer');
    const submitBtn = document.getElementById('submit-exam');
    let examInterval;
    let timeLeft = parseInt(timerElement?.getAttribute('data-remaining') || 0);
    let isFullScreen = false;
    
    // Periodic save response
    function saveResponse(questionId, response) {
        fetch(`/exams/response/${questionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ response: response })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error && data.redirect) {
                window.location.href = data.redirect;
            }
        })
        .catch(error => console.error('Error saving response:', error));
    }
    
    // Auto-save responses as the user types/selects
    document.querySelectorAll('.question-response').forEach(input => {
        if (input.type === 'radio') {
            input.addEventListener('change', function() {
                const questionId = this.getAttribute('data-question-id');
                const selectedOption = document.querySelector(`input[name="question_${questionId}"]:checked`).value;
                saveResponse(questionId, selectedOption);
            });
        } else if (input.type === 'checkbox') {
            input.addEventListener('change', function() {
                const questionId = this.getAttribute('data-question-id');
                const selectedOptions = Array.from(
                    document.querySelectorAll(`input[name="question_${questionId}[]"]:checked`)
                ).map(cb => cb.value).join(',');
                saveResponse(questionId, selectedOptions);
            });
        } else {
            // Text inputs/textareas
            let timeout;
            input.addEventListener('input', function() {
                clearTimeout(timeout);
                const questionId = this.getAttribute('data-question-id');
                timeout = setTimeout(() => {
                    saveResponse(questionId, this.value);
                }, 1000); // Save after 1 second of inactivity
            });
        }
    });
    
    // Timer functionality
    function updateTimer() {
        if (timeLeft <= 0) {
            clearInterval(examInterval);
            autoSubmitExam();
            return;
        }
        
        timeLeft--;
        
        const hours = Math.floor(timeLeft / 3600);
        const minutes = Math.floor((timeLeft % 3600) / 60);
        const seconds = timeLeft % 60;
        
        timerElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Visual warning when time is running out (less than 5 minutes)
        if (timeLeft < 300) {
            timerElement.classList.add('text-danger');
            
            // Flash the timer when less than 1 minute remains
            if (timeLeft < 60) {
                timerElement.classList.toggle('bg-danger');
                timerElement.classList.toggle('text-white');
            }
        }
    }
    
    if (timerElement) {
        // Start the timer
        examInterval = setInterval(updateTimer, 1000);
        updateTimer(); // Initial update
    }
    
    // Auto-submit when time expires
    function autoSubmitExam() {
        if (examForm) {
            alert('Time is up! Your exam is being submitted automatically.');
            examForm.submit();
        }
    }
    
    // Manual submit handling
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to submit your exam? You cannot make changes after submission.')) {
                e.preventDefault();
            }
        });
    }
    
    // Prevent tab switching, browser navigation, etc.
    let pageHidden = false;
    
    // Detect page visibility change
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            pageHidden = true;
            // Show warning when the user returns
        } else if (pageHidden) {
            alert('Warning: Leaving the exam page may result in automatic submission. Please stay focused on the exam.');
            pageHidden = false;
        }
    });
    
    // Request full screen when exam starts
    const startFullScreenBtn = document.getElementById('start-fullscreen');
    if (startFullScreenBtn) {
        startFullScreenBtn.addEventListener('click', function() {
            const examContainer = document.getElementById('exam-container');
            if (examContainer && examContainer.requestFullscreen) {
                examContainer.requestFullscreen().then(() => {
                    isFullScreen = true;
                    this.style.display = 'none';
                    document.getElementById('exam-content').style.display = 'block';
                }).catch(err => {
                    console.error('Error attempting to enable fullscreen:', err);
                    // Still show exam even if fullscreen fails
                    this.style.display = 'none';
                    document.getElementById('exam-content').style.display = 'block';
                });
            } else {
                // Fallback if fullscreen is not supported
                this.style.display = 'none';
                document.getElementById('exam-content').style.display = 'block';
            }
        });
    }
    
    // Detect fullscreen change
    document.addEventListener('fullscreenchange', function() {
        if (document.fullscreenElement === null && isFullScreen) {
            isFullScreen = false;
            alert('Warning: Exiting fullscreen mode during an exam may be recorded and reported to the administrator.');
        }
    });
    
    // Prevent keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Prevent common shortcut combinations
        if ((e.ctrlKey || e.metaKey) && 
            (e.key === 'c' || e.key === 'v' || e.key === 'a' || 
             e.key === 'p' || e.key === 's' || e.key === 'u' || 
             e.key === 'tab' || e.key === 't')) {
            e.preventDefault();
            alert('Keyboard shortcuts are disabled during the exam.');
            return false;
        }
        
        // Prevent Alt+Tab
        if (e.altKey && e.key === 'Tab') {
            e.preventDefault();
            alert('Please stay focused on the exam.');
            return false;
        }
    });
    
    // Disable right-click context menu
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Disable text selection to prevent copy-paste
    document.addEventListener('selectstart', function(e) {
        if (!e.target.matches('input, textarea')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Warn before closing or refreshing the window
    window.addEventListener('beforeunload', function(e) {
        if (examForm) {
            const message = 'Warning: Leaving this page will submit your exam automatically. Are you sure you want to proceed?';
            e.returnValue = message;
            return message;
        }
    });
});
