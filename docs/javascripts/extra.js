// Strataregula Documentation Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Add copy button functionality to code blocks
    addCopyButtons();
    
    // Add smooth scrolling for anchor links
    addSmoothScrolling();
    
    // Add interactive examples
    addInteractiveExamples();
    
    // Add performance metrics animation
    animateMetrics();
    
    // Add plugin status indicators
    updatePluginStatus();
});

function addCopyButtons() {
    // Add copy buttons to code blocks
    document.querySelectorAll('pre > code').forEach(function(codeBlock) {
        const pre = codeBlock.parentNode;
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = 'Copy';
        button.title = 'Copy to clipboard';
        
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(codeBlock.textContent).then(function() {
                button.textContent = 'Copied!';
                button.classList.add('copied');
                setTimeout(function() {
                    button.textContent = 'Copy';
                    button.classList.remove('copied');
                }, 2000);
            });
        });
        
        pre.style.position = 'relative';
        pre.appendChild(button);
    });
}

function addSmoothScrolling() {
    // Add smooth scrolling for internal links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function addInteractiveExamples() {
    // Add interactive command-line examples
    document.querySelectorAll('.command-example').forEach(function(example) {
        const commandInput = example.querySelector('.command-input');
        const output = example.querySelector('.command-output');
        
        if (commandInput && output) {
            commandInput.addEventListener('input', function() {
                // Simulate command execution
                simulateCommand(this.value, output);
            });
        }
    });
}

function simulateCommand(command, outputElement) {
    // Simple command simulation for documentation
    const responses = {
        'sr --version': 'Strataregula 0.1.1',
        'sr compile --help': `Usage: sr compile [OPTIONS] INPUT_FILE
        
Options:
  --output, -o TEXT      Output file path
  --format, -f TEXT      Output format (python, json, yaml)
  --plan                 Show expansion plan without generating
  --stats                Show compilation statistics
  --help                 Show this message and exit.`,
        'srd --version': 'DOE Runner 0.1.0',
        'srd run --help': `Usage: srd run [OPTIONS]

Options:
  --cases TEXT           Cases CSV file path
  --out TEXT            Output metrics CSV file path
  --max-workers INTEGER Number of parallel workers
  --force               Force re-execution (ignore cache)
  --dry-run             Validate without execution
  --verbose             Enable verbose output
  --help                Show this message and exit.`
    };
    
    const response = responses[command] || `Command not found: ${command}`;
    outputElement.textContent = response;
}

function animateMetrics() {
    // Animate performance metrics on scroll
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const metricValue = entry.target.querySelector('.metric-value');
                if (metricValue && !metricValue.classList.contains('animated')) {
                    animateNumber(metricValue);
                    metricValue.classList.add('animated');
                }
            }
        });
    });
    
    document.querySelectorAll('.metric-item').forEach(function(metric) {
        observer.observe(metric);
    });
}

function animateNumber(element) {
    const target = parseInt(element.textContent);
    const duration = 1500;
    const step = target / (duration / 16);
    let current = 0;
    
    const timer = setInterval(function() {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

function updatePluginStatus() {
    // Update plugin status indicators based on current state
    document.querySelectorAll('.plugin-status').forEach(function(status) {
        const text = status.textContent.toLowerCase();
        if (text.includes('stable')) {
            status.classList.add('status-stable');
        } else if (text.includes('beta')) {
            status.classList.add('status-beta');
        } else if (text.includes('alpha')) {
            status.classList.add('status-alpha');
        }
    });
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.md-search__input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close search
    if (e.key === 'Escape') {
        const searchInput = document.querySelector('.md-search__input');
        if (searchInput && document.activeElement === searchInput) {
            searchInput.blur();
        }
    }
});

// Add table of contents highlighting
function updateTocHighlight() {
    const headings = document.querySelectorAll('h2, h3, h4');
    const tocLinks = document.querySelectorAll('.md-nav--secondary a');
    
    let current = '';
    headings.forEach(function(heading) {
        const rect = heading.getBoundingClientRect();
        if (rect.top <= 100) {
            current = heading.id;
        }
    });
    
    tocLinks.forEach(function(link) {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });
}

// Update TOC highlighting on scroll
window.addEventListener('scroll', function() {
    requestAnimationFrame(updateTocHighlight);
});

// Add CSS for custom elements
const style = document.createElement('style');
style.textContent = `
.copy-button {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.25rem 0.5rem;
    background-color: var(--md-primary-fg-color);
    color: white;
    border: none;
    border-radius: 0.25rem;
    font-size: 0.8rem;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
}

pre:hover .copy-button {
    opacity: 1;
}

.copy-button:hover {
    background-color: var(--md-primary-fg-color--light);
}

.copy-button.copied {
    background-color: #4caf50;
}

.command-example {
    background-color: #263238;
    color: #eeffff;
    padding: 1rem;
    border-radius: 0.5rem;
    font-family: monospace;
    margin: 1rem 0;
}

.command-input {
    background: transparent;
    border: none;
    color: inherit;
    font-family: inherit;
    width: 100%;
    outline: none;
    font-size: 1rem;
}

.command-output {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid #37474f;
    color: #82b1ff;
    white-space: pre-wrap;
}

.md-nav--secondary a.active {
    color: var(--md-primary-fg-color);
    font-weight: 600;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.metric-item {
    animation: fadeInUp 0.6s ease-out;
}
`;
document.head.appendChild(style);