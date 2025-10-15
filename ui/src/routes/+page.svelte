<script>
    import { getVideos, uploadVideo, cancelUpload } from '../utils/fire.js';
    import { onMount } from 'svelte';

    let videoInfoPromise = getVideos()
    let selectedFile = null;
    let uploadProgress = 0;
    let fileName = '';
    
    onMount(() => {
        let authenticated = localStorage.getItem('authenticated')
        if (!authenticated) {
            window.location.href = '/login';
        }
    });

    const handleFileChange = (event) => {
        selectedFile = event.target.files[0];
        fileName = selectedFile ? selectedFile.name : '';
    };

    const handleUpload = async () => {
        if (selectedFile) {
            const updateProgress = (progress) => {
                uploadProgress = progress;
            };
            try {
                await uploadVideo(selectedFile, updateProgress);
            } catch (error) {
                console.error('Upload failed:', error);
            }
        }
    };

    const handleCancel = () => {
        uploadProgress = -1
        cancelUpload()
        selectedFile = null;
        fileName = '';
    }

    function formatDate(timestamp) {
        const date = timestamp.toDate();
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }

    function handleLogout() {
        localStorage.removeItem('authenticated');
        window.location.href = '/login';
    }
</script>

<svelte:head>
    <title>Video List - Revolution Translate</title>
</svelte:head>

{#await videoInfoPromise then videoInfo}

<div class="page-container">
    <header class="page-header">
        <div class="header-content">
            <div class="brand">
                <img src="/Revolution Church - Full Horiztonal Black SM.png" alt="Revolution Church" class="logo">
                <h1 class="page-title">Translation Portal</h1>
            </div>
            <button on:click={handleLogout} class="logout-button">Sign Out</button>
        </div>
    </header>

    <div class="main-content">
        <div class="upload-section card">
            <h2 class="section-title">Upload Video</h2>
            <div class="upload-controls">
                <div class="file-input-wrapper">
                    <input 
                        type="file" 
                        id="file-upload"
                        accept="video/*" 
                        on:change={handleFileChange}
                        class="file-input"
                    >
                    <label for="file-upload" class="file-input-label">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                        {fileName || 'Choose Video File'}
                    </label>
                </div>
                <button on:click={handleUpload} class="primary" disabled={!selectedFile || uploadProgress > 0}>
                    Upload
                </button>
            </div>

            {#if uploadProgress > 0 && uploadProgress < 100}
                <div class="upload-status">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {uploadProgress}%"></div>
                    </div>
                    <p class="progress-text">Uploading... {uploadProgress}%</p>
                    <button on:click={handleCancel} class="cancel-button">Cancel Upload</button>
                </div>
            {:else if uploadProgress === 100}
                <div class="upload-status success">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                    <div>
                        <p class="success-title">Upload complete!</p>
                        <p class="success-message">Video will be available in 15-30 minutes.</p>
                    </div>
                </div>
            {:else if uploadProgress === -1}
                <div class="upload-status cancelled">
                    <p>Upload cancelled.</p>
                </div>
            {/if}
        </div>

        <div class="video-list-section">
            <h2 class="section-title">Videos</h2>
            <div class="video-grid">
                {#each [...videoInfo] as [videoID, value] (videoID)}
                    <div class="video-card">
                        <div class="video-card-header">
                            <h3 class="video-name">{value.videoName}</h3>
                            <a 
                                class="edit-button button primary"
                                href={`/englishTranscript/${videoID}`} 
                                on:click={() => {localStorage.setItem('videoName', value.videoName);}}>
                                Edit Transcript
                            </a>
                        </div>
                        <div class="video-card-body">
                            <div class="video-meta">
                                <div class="meta-item">
                                    <span class="meta-label">Length</span>
                                    <span class="meta-value">{value.vidLength.endTime.slice(0,-4)}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Generated</span>
                                    <span class="meta-value">{formatDate(value.publishTime)}</span>
                                </div>
                            </div>
                            <div class="video-meta">
                                <div class="meta-item">
                                    <span class="meta-label">Last English Edit</span>
                                    <span class="meta-value">{formatDate(value.englishMessageData.genTime)}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Last Spanish Edit</span>
                                    <span class="meta-value">
                                        {#if value.spanishMessageData}
                                            {formatDate(value.spanishMessageData.genTime)}
                                        {:else}
                                            <span class="na">Not available</span>
                                        {/if}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    </div>

    <footer class="page-footer">
        <p>Evan Stoelzel | Minas Consulting | evan@minas.consulting</p>
    </footer>
</div>
    
{:catch error}
    <div class="error-container">
        <p class="error-message">{error.message}</p>
    </div>
{/await}

<style>
    :global(body) {
        background-color: var(--color-primary);
        color: var(--color-text);
    }

    .page-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
    }

    .page-header {
        background-color: var(--color-surface-elevated);
        border-bottom: 1px solid var(--color-border);
        padding: var(--spacing-lg) 0;
        box-shadow: var(--shadow-md);
        position: sticky;
        top: 0;
        z-index: var(--z-sticky);
    }

    .header-content {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 var(--spacing-lg);
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: var(--spacing-lg);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: var(--spacing-lg);
        flex: 1;
        min-width: 0;
    }

    .logo {
        max-width: 180px;
        height: auto;
        filter: brightness(0) invert(1);
        flex-shrink: 0;
    }

    .page-title {
        font-size: var(--font-size-2xl);
        margin: 0;
        white-space: nowrap;
    }

    .logout-button {
        flex-shrink: 0;
    }

    .main-content {
        flex: 1;
        max-width: 1400px;
        width: 100%;
        margin: 0 auto;
        padding: var(--spacing-xl) var(--spacing-lg);
    }

    .upload-section {
        margin-bottom: var(--spacing-xl);
    }

    .section-title {
        font-size: var(--font-size-2xl);
        margin-bottom: var(--spacing-lg);
    }

    .upload-controls {
        display: flex;
        gap: var(--spacing-md);
        align-items: center;
        flex-wrap: wrap;
    }

    .file-input-wrapper {
        flex: 1;
        min-width: 250px;
    }

    .file-input {
        display: none;
    }

    .file-input-label {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-md);
        background-color: var(--color-surface);
        border: 2px dashed var(--color-border);
        border-radius: var(--radius-md);
        cursor: pointer;
        transition: all var(--transition-fast);
        color: var(--color-text-secondary);
        font-weight: var(--font-weight-medium);
    }

    .file-input-label:hover {
        border-color: var(--color-accent);
        color: var(--color-accent);
    }

    .upload-status {
        margin-top: var(--spacing-lg);
        padding: var(--spacing-lg);
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
    }

    .upload-status.success {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        border-color: var(--color-success);
        background-color: rgba(76, 175, 80, 0.1);
    }

    .upload-status.success svg {
        color: var(--color-success);
        flex-shrink: 0;
    }

    .upload-status.cancelled {
        border-color: var(--color-warning);
        background-color: rgba(255, 152, 0, 0.1);
    }

    .progress-bar {
        width: 100%;
        height: 8px;
        background-color: var(--color-surface-elevated);
        border-radius: var(--radius-full);
        overflow: hidden;
        margin-bottom: var(--spacing-md);
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--color-accent) 0%, var(--color-accent-hover) 100%);
        transition: width 0.3s ease;
    }

    .progress-text {
        margin-bottom: var(--spacing-md);
        font-weight: var(--font-weight-medium);
    }

    .cancel-button {
        background-color: transparent;
        color: var(--color-error);
        border-color: var(--color-error);
    }

    .cancel-button:hover {
        background-color: rgba(244, 67, 54, 0.1);
    }

    .success-title {
        font-weight: var(--font-weight-semibold);
        color: var(--color-success);
        margin-bottom: var(--spacing-xs);
    }

    .success-message {
        color: var(--color-text-secondary);
        margin: 0;
    }

    .video-list-section {
        margin-bottom: var(--spacing-2xl);
    }

    .video-grid {
        display: grid;
        gap: var(--spacing-lg);
        grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
    }

    .video-card {
        background-color: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        overflow: hidden;
        transition: all var(--transition-fast);
    }

    .video-card:hover {
        border-color: var(--color-border-light);
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    .video-card-header {
        padding: var(--spacing-lg);
        background-color: var(--color-surface);
        border-bottom: 1px solid var(--color-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: var(--spacing-md);
    }

    .video-name {
        font-size: var(--font-size-lg);
        margin: 0;
        word-break: break-word;
        flex: 1;
    }

    .edit-button {
        flex-shrink: 0;
        padding: var(--spacing-sm) var(--spacing-md);
        font-size: var(--font-size-sm);
    }

    .video-card-body {
        padding: var(--spacing-lg);
        display: flex;
        flex-direction: column;
        gap: var(--spacing-md);
    }

    .video-meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--spacing-md);
    }

    .meta-item {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);
    }

    .meta-label {
        font-size: var(--font-size-xs);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .meta-value {
        font-size: var(--font-size-sm);
        color: var(--color-text);
        font-weight: var(--font-weight-medium);
    }

    .na {
        color: var(--color-text-muted);
        font-style: italic;
    }

    .page-footer {
        background-color: var(--color-surface-elevated);
        border-top: 1px solid var(--color-border);
        padding: var(--spacing-lg);
        text-align: center;
    }

    .page-footer p {
        margin: 0;
        color: var(--color-text-muted);
        font-size: var(--font-size-sm);
    }

    .error-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: var(--spacing-lg);
    }

    .error-message {
        color: var(--color-error);
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-medium);
    }

    @media (max-width: 768px) {
        .header-content {
            flex-direction: column;
            align-items: stretch;
        }

        .brand {
            flex-direction: column;
            align-items: center;
            text-align: center;
        }

        .page-title {
            font-size: var(--font-size-xl);
        }

        .video-grid {
            grid-template-columns: 1fr;
        }

        .video-card-header {
            flex-direction: column;
            align-items: stretch;
        }

        .edit-button {
            width: 100%;
        }

        .upload-controls {
            flex-direction: column;
            align-items: stretch;
        }

        .file-input-wrapper {
            min-width: 100%;
        }
    }

    @media (max-width: 480px) {
        .logo {
            max-width: 140px;
        }

        .video-meta {
            grid-template-columns: 1fr;
        }
    }
</style>
