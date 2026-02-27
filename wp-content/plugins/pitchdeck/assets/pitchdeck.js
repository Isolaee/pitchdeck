/* pitchdeck.js — upload PPTX, render extracted slides, save extra info */
(function () {
    'use strict';

    // pitchdeck_config is injected by wp_localize_script in pitchdeck.php
    const { rest_url, nonce } = window.pitchdeck_config;

    let currentJobId = null;
    let currentSlides = [];

    document.addEventListener('DOMContentLoaded', function () {
        const form        = document.getElementById('pitchdeck-upload-form');
        const saveBtn     = document.getElementById('pitchdeck-save-btn');
        const generateBtn = document.getElementById('pitchdeck-generate-btn');
        if (form)        form.addEventListener('submit', handleUpload);
        if (saveBtn)     saveBtn.addEventListener('click', handleSave);
        if (generateBtn) generateBtn.addEventListener('click', handleGenerateScript);
    });

    /**
     * Handle PPTX upload form submission.
     * Sends multipart/form-data to POST /wp-json/pitchdeck/v1/upload
     */
    async function handleUpload(event) {
        event.preventDefault();

        const fileInput      = document.getElementById('pitchdeck-file');
        const slidesContainer = document.getElementById('pitchdeck-slides-container');
        const saveSection    = document.getElementById('pitchdeck-save-section');

        if (!fileInput.files.length) {
            setStatus('Please select a .pptx file.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('pptx_file', fileInput.files[0]);

        setStatus('Uploading and extracting slides\u2026', 'info');
        slidesContainer.innerHTML = '';
        saveSection.style.display = 'none';

        try {
            const response = await fetch(`${rest_url}/upload`, {
                method: 'POST',
                headers: { 'X-WP-Nonce': nonce },
                // Do NOT set Content-Type — browser sets the multipart boundary automatically.
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                setStatus(`Error: ${data.message || 'Upload failed.'}`, 'error');
                return;
            }

            currentJobId  = data.job_id;
            currentSlides = data.slides;

            renderSlides(data.slides);
            setStatus(
                `Extracted ${data.slides.length} slide(s). Add notes below, then click Save.`,
                'success'
            );
            saveSection.style.display = 'block';

        } catch (err) {
            setStatus('Upload failed: ' + err.message, 'error');
            console.error('Pitchdeck upload error:', err);
        }
    }

    /**
     * Render extracted slides as cards: extracted text + extra-info textarea.
     */
    function renderSlides(slides) {
        const container = document.getElementById('pitchdeck-slides-container');
        container.innerHTML = '';

        slides.forEach(function (slide) {
            const card = document.createElement('div');
            card.className = 'pitchdeck-slide';
            card.dataset.slideNumber = slide.slide_number;

            card.innerHTML = `
                <h3>Slide ${slide.slide_number}</h3>
                <div class="pitchdeck-slide-text">
                    <strong>Extracted text:</strong>
                    <pre>${escapeHtml(slide.slide_text || '(no text found)')}</pre>
                </div>
                <div class="pitchdeck-extra-info">
                    <label for="extra-info-${slide.slide_number}">Extra notes / context:</label>
                    <textarea
                        id="extra-info-${slide.slide_number}"
                        rows="3"
                        placeholder="Add speaker context or additional information for this slide\u2026"
                    >${escapeHtml(slide.extra_info || '')}</textarea>
                </div>`;

            container.appendChild(card);
        });
    }

    /**
     * Collect textarea values and POST to /save-slides.
     */
    async function handleSave() {
        if (!currentJobId || !currentSlides.length) {
            setStatus('No slides loaded. Please upload a file first.', 'error');
            return;
        }

        const slidesToSave = currentSlides.map(function (slide) {
            const textarea = document.getElementById(`extra-info-${slide.slide_number}`);
            return {
                slide_number: slide.slide_number,
                slide_text:   slide.slide_text,
                extra_info:   textarea ? textarea.value : '',
            };
        });

        setStatus('Saving\u2026', 'info');

        try {
            const response = await fetch(`${rest_url}/save-slides`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-WP-Nonce':   nonce,
                },
                body: JSON.stringify({ job_id: currentJobId, slides: slidesToSave }),
            });

            const data = await response.json();

            if (!response.ok) {
                setStatus(`Save failed: ${data.message || 'Unknown error.'}`, 'error');
                return;
            }

            setStatus(
                `Saved ${data.saved_count} slide(s). Now click Generate Script to create voiceover scripts.`,
                'success'
            );

            // Show the Generate Script button after a successful save.
            const generateBtn = document.getElementById('pitchdeck-generate-btn');
            if (generateBtn) generateBtn.style.display = 'inline-block';

        } catch (err) {
            setStatus('Network error during save. Please try again.', 'error');
            console.error('Pitchdeck save error:', err);
        }
    }

    /**
     * Call POST /generate-script, then render the returned scripts per slide.
     */
    async function handleGenerateScript() {
        if (!currentJobId) {
            setStatus('No job loaded. Please upload and save slides first.', 'error');
            return;
        }

        const generateBtn   = document.getElementById('pitchdeck-generate-btn');
        const scriptSection = document.getElementById('pitchdeck-script-section');

        generateBtn.disabled = true;
        setStatus('Generating scripts via OpenAI\u2026 this may take a few seconds.', 'info');

        try {
            const response = await fetch(`${rest_url}/generate-script`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-WP-Nonce':   nonce,
                },
                body: JSON.stringify({ job_id: currentJobId }),
            });

            const data = await response.json();

            if (!response.ok) {
                setStatus(`Script generation failed: ${data.message || 'Unknown error.'}`, 'error');
                return;
            }

            renderScripts(data.scripts);
            scriptSection.style.display = 'block';
            setStatus(`Scripts generated for ${data.scripts.length} slide(s). Review and edit below.`, 'success');

        } catch (err) {
            setStatus('Network error during script generation. Please try again.', 'error');
            console.error('Pitchdeck generate error:', err);
        } finally {
            generateBtn.disabled = false;
        }
    }

    /**
     * Render generated scripts as editable textareas, one per slide.
     */
    function renderScripts(scripts) {
        const container = document.getElementById('pitchdeck-scripts-container');
        container.innerHTML = '';

        scripts.forEach(function (item) {
            const card = document.createElement('div');
            card.className = 'pitchdeck-script-card';

            card.innerHTML = `
                <h3>Slide ${item.slide_number}</h3>
                <textarea
                    id="script-text-${item.slide_number}"
                    class="pitchdeck-script-textarea"
                    rows="4"
                >${escapeHtml(item.script_text || '')}</textarea>`;

            container.appendChild(card);
        });
    }

    function setStatus(message, type) {
        const el = document.getElementById('pitchdeck-status');
        if (el) {
            el.textContent = message;
            el.className   = `pitchdeck-status pitchdeck-status--${type}`;
        }
    }

    /** Minimal HTML escaping to prevent XSS in rendered slide text. */
    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
})();
