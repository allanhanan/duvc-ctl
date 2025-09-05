/* ============================================================================
   duvc-ctl Documentation - Interactive Features
   ============================================================================ */

(function() {
    'use strict';
    
    // ========================================================================
    // Theme Management System
    // ========================================================================
    
    class ThemeManager {
        constructor() {
            this.currentTheme = localStorage.getItem('duvc-theme') || 'auto';
            this.currentColorScheme = localStorage.getItem('duvc-color-scheme') || 'blue';
            this.init();
        }
        
        init() {
            this.applyTheme();
            this.createThemeToggle();
            this.createColorSchemeSelector();
            this.bindEvents();
        }
        
        applyTheme() {
            const root = document.documentElement;
            
            if (this.currentTheme === 'auto') {
                root.removeAttribute('data-theme');
            } else {
                root.setAttribute('data-theme', this.currentTheme);
            }
            
            root.setAttribute('data-color-scheme', this.currentColorScheme);
        }
        
        createThemeToggle() {
            const toggle = document.createElement('button');
            toggle.className = 'theme-toggle';
            toggle.setAttribute('aria-label', 'Toggle dark mode');
            toggle.setAttribute('title', 'Toggle dark mode');
            toggle.addEventListener('click', () => this.toggleTheme());
            
            document.body.appendChild(toggle);
        }
        
        createColorSchemeSelector() {
            const selector = document.createElement('div');
            selector.className = 'theme-selector';
            selector.innerHTML = `
                <h4>Color Scheme</h4>
                <div class="theme-options">
                    <div class="theme-option" data-color="blue" title="Blue"></div>
                    <div class="theme-option" data-color="green" title="Green"></div>
                    <div class="theme-option" data-color="purple" title="Purple"></div>
                    <div class="theme-option" data-color="orange" title="Orange"></div>
                    <div class="theme-option" data-color="red" title="Red"></div>
                    <div class="theme-option" data-color="teal" title="Teal"></div>
                </div>
            `;
            
            document.body.appendChild(selector);
            this.updateColorSchemeSelector();
            
            // Double-click theme toggle to show color selector
            const themeToggle = document.querySelector('.theme-toggle');
            let clickCount = 0;
            themeToggle.addEventListener('click', () => {
                clickCount++;
                if (clickCount === 2) {
                    selector.classList.toggle('show');
                    clickCount = 0;
                }
                setTimeout(() => { clickCount = 0; }, 300);
            });
        }
        
        toggleTheme() {
            const themes = ['auto', 'light', 'dark'];
            const currentIndex = themes.indexOf(this.currentTheme);
            this.currentTheme = themes[(currentIndex + 1) % themes.length];
            
            localStorage.setItem('duvc-theme', this.currentTheme);
            this.applyTheme();
        }
        
        setColorScheme(scheme) {
            this.currentColorScheme = scheme;
            localStorage.setItem('duvc-color-scheme', scheme);
            this.applyTheme();
            this.updateColorSchemeSelector();
        }
        
        updateColorSchemeSelector() {
            const options = document.querySelectorAll('.theme-option');
            options.forEach(option => {
                option.classList.remove('active');
                if (option.dataset.color === this.currentColorScheme) {
                    option.classList.add('active');
                }
            });
        }
        
        bindEvents() {
            document.addEventListener('click', (e) => {
                if (e.target.classList.contains('theme-option')) {
                    this.setColorScheme(e.target.dataset.color);
                }
                
                // Close color selector when clicking outside
                if (!e.target.closest('.theme-selector') && !e.target.closest('.theme-toggle')) {
                    document.querySelector('.theme-selector').classList.remove('show');
                }
            });
        }
    }
    
    // ========================================================================
    // Enhanced Copy Code Functionality
    // ========================================================================
    
    class CodeCopyManager {
        constructor() {
            this.init();
        }
        
        init() {
            this.enhanceCodeBlocks();
            this.addCopyFunctionality();
        }
        
        enhanceCodeBlocks() {
            const codeBlocks = document.querySelectorAll('.highlight');
            
            codeBlocks.forEach((block, index) => {
                // Add language detection
                const code = block.querySelector('code, pre');
                if (code) {
                    const className = code.className;
                    const langMatch = className.match(/language-(\w+)|highlight-(\w+)/);
                    if (langMatch) {
                        const lang = langMatch[1] || langMatch[2];
                        block.setAttribute('data-language', lang);
                    }
                }
                
                // Add unique ID for referencing
                block.setAttribute('data-code-block', index);
                
                // Add line numbers for longer code blocks
                const lines = block.textContent.split('\n').length;
                if (lines > 5) {
                    this.addLineNumbers(block);
                }
            });
        }
        
        addLineNumbers(block) {
            const pre = block.querySelector('pre');
            if (!pre) return;
            
            const lines = pre.textContent.split('\n');
            const lineNumbersContainer = document.createElement('div');
            lineNumbersContainer.className = 'line-numbers';
            lineNumbersContainer.innerHTML = lines.map((_, i) => `<span>${i + 1}</span>`).join('');
            
            block.classList.add('has-line-numbers');
            block.insertBefore(lineNumbersContainer, pre);
        }
        
        addCopyFunctionality() {
            // Enhanced copy buttons
            document.addEventListener('click', (e) => {
                if (e.target.classList.contains('copybtn') || e.target.closest('.copybtn')) {
                    e.preventDefault();
                    const button = e.target.closest('.copybtn') || e.target;
                    this.copyCode(button);
                }
            });
        }
        
        async copyCode(button) {
            const codeBlock = button.closest('.highlight');
            if (!codeBlock) return;
            
            const code = codeBlock.querySelector('pre').textContent;
            
            try {
                await navigator.clipboard.writeText(code);
                this.showCopyFeedback(button, 'Copied!');
            } catch (err) {
                // Fallback for older browsers
                this.fallbackCopy(code);
                this.showCopyFeedback(button, 'Copied!');
            }
        }
        
        fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }
        
        showCopyFeedback(button, message) {
            const originalHTML = button.innerHTML;
            button.innerHTML = message;
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);
        }
    }
    
    // ========================================================================
    // Smooth Scrolling & Navigation Enhancement
    // ========================================================================
    
    class NavigationEnhancer {
        constructor() {
            this.init();
        }
        
        init() {
            this.enhanceTOC();
            this.addBackToTop();
            this.addScrollProgress();
            this.enhanceAnchorLinks();
        }
        
        enhanceTOC() {
            const toc = document.querySelector('.wy-menu-vertical');
            if (!toc) return;
            
            // Add section indicators
            const currentPage = window.location.pathname;
            const tocLinks = toc.querySelectorAll('a');
            
            tocLinks.forEach(link => {
                if (link.getAttribute('href') === currentPage || 
                    link.getAttribute('href').endsWith(currentPage)) {
                    link.classList.add('current-page');
                }
            });
            
            // Add smooth scrolling to internal links
            tocLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('#')) {
                    link.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.scrollToElement(href.substring(1));
                    });
                }
            });
        }
        
        addBackToTop() {
            const backToTop = document.createElement('button');
            backToTop.innerHTML = '↑';
            backToTop.className = 'back-to-top';
            backToTop.setAttribute('aria-label', 'Back to top');
            backToTop.style.cssText = `
                position: fixed;
                bottom: 80px;
                right: 20px;
                width: 50px;
                height: 50px;
                border: none;
                border-radius: 50%;
                background: var(--duvc-primary);
                color: white;
                font-size: 1.5rem;
                cursor: pointer;
                opacity: 0;
                transform: scale(0);
                transition: all 0.3s ease;
                z-index: 999;
                box-shadow: var(--duvc-shadow);
            `;
            
            document.body.appendChild(backToTop);
            
            backToTop.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
            
            // Show/hide based on scroll position
            window.addEventListener('scroll', () => {
                if (window.pageYOffset > 300) {
                    backToTop.style.opacity = '1';
                    backToTop.style.transform = 'scale(1)';
                } else {
                    backToTop.style.opacity = '0';
                    backToTop.style.transform = 'scale(0)';
                }
            });
        }
        
        addScrollProgress() {
            const progressBar = document.createElement('div');
            progressBar.className = 'scroll-progress';
            progressBar.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 0%;
                height: 3px;
                background: var(--duvc-primary);
                z-index: 1001;
                transition: width 0.1s ease;
            `;
            
            document.body.appendChild(progressBar);
            
            window.addEventListener('scroll', () => {
                const scrolled = (window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
                progressBar.style.width = Math.min(scrolled, 100) + '%';
            });
        }
        
        enhanceAnchorLinks() {
            // Add click handlers to all anchor links
            document.addEventListener('click', (e) => {
                const link = e.target.closest('a[href^="#"]');
                if (link) {
                    e.preventDefault();
                    const targetId = link.getAttribute('href').substring(1);
                    this.scrollToElement(targetId);
                }
            });
            
            // Add hover effects to headings with anchors
            const headings = document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]');
            headings.forEach(heading => {
                heading.style.position = 'relative';
                heading.addEventListener('mouseenter', () => {
                    const anchor = document.createElement('a');
                    anchor.href = '#' + heading.id;
                    anchor.innerHTML = '🔗';
                    anchor.className = 'heading-anchor';
                    anchor.style.cssText = `
                        position: absolute;
                        left: -25px;
                        top: 50%;
                        transform: translateY(-50%);
                        opacity: 0.6;
                        text-decoration: none;
                        font-size: 0.8em;
                        transition: opacity 0.2s ease;
                    `;
                    heading.appendChild(anchor);
                });
                
                heading.addEventListener('mouseleave', () => {
                    const anchor = heading.querySelector('.heading-anchor');
                    if (anchor) anchor.remove();
                });
            });
        }
        
        scrollToElement(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                const offsetTop = element.offsetTop - 80; // Account for fixed header
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Update URL
                history.pushState(null, null, '#' + elementId);
            }
        }
    }
    
    // ========================================================================
    // Search Enhancement
    // ========================================================================
    
    class SearchEnhancer {
        constructor() {
            this.init();
        }
        
        init() {
            this.enhanceSearchBox();
            this.addKeyboardShortcuts();
        }
        
        enhanceSearchBox() {
            const searchInput = document.querySelector('input[type="search"], input[name="q"]');
            if (!searchInput) return;
            
            // Add search suggestions
            searchInput.addEventListener('input', this.debounce((e) => {
                this.handleSearchInput(e.target.value);
            }, 300));
            
            // Add clear button
            const clearButton = document.createElement('button');
            clearButton.innerHTML = '×';
            clearButton.className = 'search-clear';
            clearButton.style.cssText = `
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                opacity: 0.6;
                color: var(--duvc-text-light);
            `;
            
            searchInput.parentNode.style.position = 'relative';
            searchInput.parentNode.appendChild(clearButton);
            
            clearButton.addEventListener('click', () => {
                searchInput.value = '';
                searchInput.focus();
            });
        }
        
        addKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + K to focus search
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    const searchInput = document.querySelector('input[type="search"], input[name="q"]');
                    if (searchInput) {
                        searchInput.focus();
                        searchInput.select();
                    }
                }
                
                // Escape to clear search
                if (e.key === 'Escape') {
                    const searchInput = document.querySelector('input[type="search"], input[name="q"]');
                    if (searchInput && document.activeElement === searchInput) {
                        searchInput.value = '';
                        searchInput.blur();
                    }
                }
            });
        }
        
        handleSearchInput(value) {
            // This could be enhanced with real-time search suggestions
            console.log('Search query:', value);
        }
        
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    }
    
    // ========================================================================
    // Performance Monitoring
    // ========================================================================
    
    class PerformanceMonitor {
        constructor() {
            this.init();
        }
        
        init() {
            this.measurePageLoad();
            this.lazyLoadImages();
            this.optimizeAnimations();
        }
        
        measurePageLoad() {
            window.addEventListener('load', () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                
                if (loadTime > 3000) {
                    console.warn('Page load time is slow:', loadTime + 'ms');
                }
            });
        }
        
        lazyLoadImages() {
            if ('IntersectionObserver' in window) {
                const images = document.querySelectorAll('img[data-src]');
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            img.classList.add('loaded');
                            imageObserver.unobserve(img);
                        }
                    });
                });
                
                images.forEach(img => imageObserver.observe(img));
            }
        }
        
        optimizeAnimations() {
            // Pause animations for users who prefer reduced motion
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                document.documentElement.style.setProperty('--animation-duration', '0.01ms');
            }
        }
    }
    
    // ========================================================================
    // Initialization
    // ========================================================================
    
    document.addEventListener('DOMContentLoaded', () => {
        // Initialize all components
        new ThemeManager();
        new CodeCopyManager();
        new NavigationEnhancer();
        new SearchEnhancer();
        new PerformanceMonitor();
        
        // Add loading animation removal
        document.body.classList.add('loaded');
        
        // Console greeting
        console.log('%c🚀 duvc-ctl Documentation', 'color: #2196f3; font-size: 16px; font-weight: bold;');
        console.log('%cThank you for using duvc-ctl! Report issues at: https://github.com/allanhanan/duvc-ctl/issues', 'color: #666;');
    });
    
    // ========================================================================
    // Analytics & Error Reporting (Optional)
    // ========================================================================
    
    window.addEventListener('error', (e) => {
        console.error('Documentation error:', e.error);
        // This could send errors to your analytics service
    });
    
})();
