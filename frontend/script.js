(function() {
    'use strict';

    // --- DOM Elements ---
    const reviewText = document.getElementById('reviewText');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loading = document.getElementById('loading');
    const stars = document.querySelectorAll('.star');
    const ratingValue = document.getElementById('ratingValue');
    let selectedRating = null;

    // Results elements
    const positiveCount = document.getElementById('positiveCount');
    const negativeCount = document.getElementById('negativeCount');
    const neutralCount = document.getElementById('neutralCount');
    const aspectList = document.getElementById('aspectList');

    // Gauge elements
    const needle = document.getElementById('needle');
    const score = document.getElementById('score');
    const slider = document.getElementById('slider');
    const sliderValue = document.getElementById('sliderValue');
    const mouth = document.getElementById('mouth');
    const leftEye = document.querySelector('.eye.left');
    const rightEye = document.querySelector('.eye.right');

    // --- Gauge State ---
    let currentValue = 50;
    const COLORS = {
        red: '#F4510B',
        yellow: '#F8B20A',
        green: '#45C000'
    };

    // --- Star Rating ---
    stars.forEach(star => {
        star.addEventListener('click', function() {
            const value = parseInt(this.dataset.value);
            
            stars.forEach(s => s.classList.remove('active'));
            
            for (let i = 0; i < value; i++) {
                stars[i].classList.add('active');
            }
            
            selectedRating = value;
            ratingValue.textContent = value + ' ★';
        });
    });

    // --- Gauge Functions ---
    function valueToAngle(value) {
        const clamped = Math.max(0, Math.min(100, value));
        return -90 + (clamped / 100) * 180;
    }

    function getColor(value) {
        if (value <= 33) return COLORS.red;
        if (value <= 66) return COLORS.yellow;
        return COLORS.green;
    }

    function updateFace(value) {
        const color = getColor(value);

        leftEye.setAttribute('stroke', color);
        rightEye.setAttribute('stroke', color);

        let d = '';
        if (value <= 33) {
            d = 'M 35 65 Q 50 80 65 65';
        } else if (value <= 66) {
            d = 'M 35 65 Q 50 72 65 65';
        } else {
            d = 'M 35 65 Q 50 50 65 65';
        }
        mouth.setAttribute('d', d);
        mouth.setAttribute('stroke', color);
    }

    function updateGauge(value) {
        const clamped = Math.max(0, Math.min(100, value));
        const angle = valueToAngle(clamped);

        needle.style.transform = 'translateX(-50%) rotate(' + angle + 'deg)';
        score.textContent = Math.round(clamped);
        updateFace(clamped);
        currentValue = clamped;
    }

    window.setMood = function(value) {
        const clamped = Math.max(0, Math.min(100, value));
        updateGauge(clamped);
        if (slider) slider.value = clamped;
        if (sliderValue) sliderValue.textContent = Math.round(clamped);
    };

    window.getMood = function() {
        return currentValue;
    };

    // --- Slider ---
    if (slider) {
        slider.addEventListener('input', function(e) {
            const val = parseFloat(e.target.value);
            if (sliderValue) sliderValue.textContent = Math.round(val);
            updateGauge(val);
        });
    }

    // --- Keyboard controls for gauge ---
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
            e.preventDefault();
            setMood(Math.min(100, currentValue + 5));
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
            e.preventDefault();
            setMood(Math.max(0, currentValue - 5));
        }
    });

    // --- API Call to Backend ---
    async function analyzeReview() {
        const text = reviewText.value.trim();
        if (!text) {
            alert('Please enter a review.');
            return;
        }

        // Disable button and show loading
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = '⏳ Analyzing...';
        loading.style.display = 'block';

        try {
            const response = await fetch('http://localhost:8000/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    star_rating: selectedRating || null,
                    threshold: 0.55
                })
            });

            if (!response.ok) {
                throw new Error('API error: ' + response.status);
            }

            const data = await response.json();
            displayResults(data);
            
            // Update gauge based on sentiment score
            calculateAndSetMood(data);

        } catch (error) {
            console.error('Error:', error);
            alert('Error connecting to backend. Make sure the server is running on http://localhost:8000');
            
            // Fallback: Demo mode
            demoMode(text);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = '🔍 Analyze Review';
            loading.style.display = 'none';
        }
    }

    // --- Display Results ---
    function displayResults(data) {
        // Update sentiment counts
        positiveCount.textContent = data.sentiment_counts?.positive || 0;
        negativeCount.textContent = data.sentiment_counts?.negative || 0;
        neutralCount.textContent = data.sentiment_counts?.neutral || 0;

        // Update aspect list
        aspectList.innerHTML = '';
        
        if (data.aspects && data.aspects.length > 0) {
            data.aspects.forEach(aspect => {
                if (aspect === 'none') return;
                
                const sentiment = data.aspect_sentiments?.[aspect] || 'neutral';
                const div = document.createElement('div');
                div.className = `aspect-item ${sentiment}`;
                
                const icons = {
                    food: '🍽️',
                    service: '🤝',
                    price: '💰',
                    cleanliness: '🧹',
                    delivery: '🛵',
                    ambiance: '✨',
                    app_experience: '📱',
                    general: '💬'
                };
                
                div.innerHTML = `
                    <span class="aspect-icon">${icons[aspect] || '📌'}</span>
                    <span class="aspect-name">${aspect.charAt(0).toUpperCase() + aspect.slice(1)}</span>
                    <span class="aspect-sentiment">${sentiment}</span>
                `;
                aspectList.appendChild(div);
            });
        } else {
            const div = document.createElement('div');
            div.className = 'aspect-item neutral';
            div.innerHTML = `
                <span class="aspect-icon">📌</span>
                <span class="aspect-name">No aspects detected</span>
                <span class="aspect-sentiment">—</span>
            `;
            aspectList.appendChild(div);
        }

        // Update result boxes highlight
        updateResultHighlights(data);
    }

    function updateResultHighlights(data) {
        const counts = data.sentiment_counts || { positive: 0, negative: 0, neutral: 0 };
        
        document.querySelectorAll('.result-box').forEach(box => {
            box.style.opacity = '0.5';
        });
        
        if (counts.positive > 0) {
            document.querySelector('.result-box.positive').style.opacity = '1';
        }
        if (counts.negative > 0) {
            document.querySelector('.result-box.negative').style.opacity = '1';
        }
        if (counts.neutral > 0) {
            document.querySelector('.result-box.neutral').style.opacity = '1';
        }
    }

    // --- Calculate mood from sentiment ---
    function calculateAndSetMood(data) {
        const counts = data.sentiment_counts || { positive: 0, negative: 0, neutral: 0 };
        const total = counts.positive + counts.negative + counts.neutral;
        
        if (total === 0) {
            setMood(50);
            return;
        }
        
        // Calculate weighted score: positive = 100, neutral = 50, negative = 0
        const score = (counts.positive * 100 + counts.neutral * 50) / total;
        setMood(score);
    }

    // --- Fallback Demo Mode (when backend is not available) ---
    function demoMode(text) {
        // Simple keyword-based demo
        const textLower = text.toLowerCase();
        let aspects = [];
        const aspectKeywords = {
            food: ['اكل', 'طعام', 'food', 'akl', 'الاكل'],
            service: ['خدمة', 'service', '5idma', 'الخدمة'],
            price: ['سعر', 'price', 'غالي', 'رخيص'],
            cleanliness: ['نظافة', 'clean', 'نظيف', 'nadeef'],
            delivery: ['توصيل', 'delivery', 'toseel'],
            ambiance: ['جو', 'ambiance', 'ديكور'],
            app_experience: ['تطبيق', 'app', 'موقع'],
            general: ['عام', 'overall', 'تجربة']
        };

        const positiveWords = ['حلو', 'ممتاز', 'رائع', 'good', 'great', 'kwayes', 'gamed', 'جميل', 'كويس', 'تمام'];
        const negativeWords = ['وحش', 'سيء', 'bad', 'terrible', 'mish', 'زفت', 'بايظ', 'غلط'];

        for (const [aspect, keywords] of Object.entries(aspectKeywords)) {
            if (keywords.some(kw => textLower.includes(kw))) {
                aspects.push(aspect);
            }
        }

        if (aspects.length === 0) {
            aspects = ['general'];
        }

        const sentiments = {};
        let positiveScore = 0;
        let totalScore = 0;

        for (const aspect of aspects) {
            let pos = positiveWords.filter(w => textLower.includes(w)).length;
            let neg = negativeWords.filter(w => textLower.includes(w)).length;
            
            if (selectedRating) {
                if (selectedRating >= 4) pos += 2;
                else if (selectedRating <= 2) neg += 2;
            }

            if (pos > neg) {
                sentiments[aspect] = 'positive';
                positiveScore += 100;
            } else if (neg > pos) {
                sentiments[aspect] = 'negative';
                positiveScore += 0;
            } else {
                sentiments[aspect] = 'neutral';
                positiveScore += 50;
            }
            totalScore += 1;
        }

        const avgScore = totalScore > 0 ? positiveScore / totalScore : 50;

        const data = {
            aspects: aspects,
            aspect_sentiments: sentiments,
            sentiment_counts: {
                positive: Object.values(sentiments).filter(s => s === 'positive').length,
                negative: Object.values(sentiments).filter(s => s === 'negative').length,
                neutral: Object.values(sentiments).filter(s => s === 'neutral').length
            }
        };

        displayResults(data);
        setMood(avgScore);
    }

    // --- Analyze Button ---
    analyzeBtn.addEventListener('click', analyzeReview);

    // --- Enter key support ---
    reviewText.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            analyzeReview();
        }
    });

    // --- Initialize ---
    updateGauge(50);
    if (slider) slider.value = 50;
    if (sliderValue) sliderValue.textContent = '50';

    console.log('✅ Franco-Arabic ABSA ready!');
    console.log('📌 Backend URL: http://localhost:8000');
    console.log('📌 Usage: Enter a review and click Analyze');

    // --- Auto-analyze example on load ---
    setTimeout(() => {
        analyzeReview();
    }, 500);

})();