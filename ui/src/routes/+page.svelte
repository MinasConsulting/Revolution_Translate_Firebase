<script>
    import { getVideos, uploadVideo, cancelUpload, renameVideo, deleteVideo } from '../utils/fire.js';
    import { onMount } from 'svelte';

    let videoInfoPromise = $state(getVideos());
    let selectedFile = $state(null);
    let uploadProgress = $state(0);
    let fileName = $state('');
    
    let showRenameModal = $state(false);
    let showDeleteModal = $state(false);
    let selectedVideoID = $state(null);
    let selectedVideoName = $state('');
    let newVideoName = $state('');
    let isProcessing = $state(false);
    
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

    const handleReset = () => {
        uploadProgress = 0;
        selectedFile = null;
        fileName = '';
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

    function openRenameModal(videoID, videoName) {
        selectedVideoID = videoID;
        selectedVideoName = videoName;
        newVideoName = videoName;
        showRenameModal = true;
    }

    function openDeleteModal(videoID, videoName) {
        selectedVideoID = videoID;
        selectedVideoName = videoName;
        showDeleteModal = true;
    }

    function closeModals() {
        showRenameModal = false;
        showDeleteModal = false;
        selectedVideoID = null;
        selectedVideoName = '';
        newVideoName = '';
    }

    async function handleRename() {
        if (!newVideoName.trim() || newVideoName === selectedVideoName) {
            closeModals();
            return;
        }
        isProcessing = true;
        try {
            await renameVideo(selectedVideoID, newVideoName);
            videoInfoPromise = getVideos();
            closeModals();
        } catch (error) {
            console.error('Rename failed:', error);
            alert('Failed to rename video');
        } finally {
            isProcessing = false;
        }
    }

    async function handleDelete() {
        isProcessing = true;
        try {
            await deleteVideo(selectedVideoID);
            videoInfoPromise = getVideos();
            closeModals();
        } catch (error) {
            console.error('Delete failed:', error);
            alert('Failed to delete video');
        } finally {
            isProcessing = false;
        }
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
            <button onclick={handleLogout} class="logout-button">Sign Out</button>
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
                        onchange={handleFileChange}
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
                <button onclick={handleUpload} class="primary" disabled={!selectedFile || uploadProgress > 0}>
                    Upload
                </button>
            </div>

            {#if uploadProgress > 0 && uploadProgress < 100}
                <div class="upload-status">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {uploadProgress}%"></div>
                    </div>
                    <p class="progress-text">Uploading... {uploadProgress}%</p>
                    <button onclick={handleCancel} class="cancel-button">Cancel Upload</button>
                </div>
            {:else if uploadProgress === 100}
                <div class="upload-status success">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                    <div class="success-content">
                        <p class="success-title">Video upload complete</p>
                        <p class="success-message">Your video has been successfully uploaded and is being processed.</p>
                    </div>
                    <button onclick={handleReset} class="done-button">Reset Form</button>
                </div>
            {:else if uploadProgress === -1}
                <div class="upload-status cancelled">
                    <p>Upload cancelled.</p>
                </div>
            {/if}
        </div>

        <div class="video-list-section">
            <h2 class="section-title">Videos</h2>
            <div class="video-table-wrapper">
                <table class="video-table">
                    <thead>
                        <tr>
                            <th>Video Name</th>
                            <th>Actions</th>
                            <th>Length</th>
                            <th>Generated Time</th>
                            <th>Last English Edit</th>
                            <th>Last Spanish Edit</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each [...videoInfo] as [videoID, value] (videoID)}
                            <tr class="video-row">
                                <td class="video-name-cell">{value.videoName}</td>
                                <td class="action-cell">
                                    <a 
                                        class="edit-button"
                                        href={`/englishTranscript/${videoID}`} 
                                        onclick={() => {localStorage.setItem('videoName', value.videoName);}}>
                                        Edit
                                    </a>
                                    <button 
                                        class="rename-button"
                                        onclick={() => openRenameModal(videoID, value.videoName)}>
                                        Rename
                                    </button>
                                    <button 
                                        class="delete-button"
                                        onclick={() => openDeleteModal(videoID, value.videoName)}>
                                        Delete
                                    </button>
                                </td>
                                <td>{value.vidLength.endTime.slice(0,-4)}</td>
                                <td>{formatDate(value.publishTime)}</td>
                                <td>{formatDate(value.englishMessageData.genTime)}</td>
                                <td>
                                    {#if value.spanishMessageData}
                                        {formatDate(value.spanishMessageData.genTime)}
                                    {:else}
                                        <span class="na">Not available</span>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
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

{#if showRenameModal}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="modal-overlay" onclick={closeModals}>
        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="rename-title" onclick={(e) => e.stopPropagation()}>
            <h3 id="rename-title" class="modal-title">Rename Video</h3>
            <p class="modal-subtitle">Current name: {selectedVideoName}</p>
            <input 
                type="text" 
                class="modal-input"
                bind:value={newVideoName}
                placeholder="Enter new name"
            />
            <div class="modal-actions">
                <button class="modal-cancel" onclick={closeModals} disabled={isProcessing}>Cancel</button>
                <button class="modal-confirm" onclick={handleRename} disabled={isProcessing}>
                    {isProcessing ? 'Renaming...' : 'Rename'}
                </button>
            </div>
        </div>
    </div>
{/if}

{#if showDeleteModal}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="modal-overlay" onclick={closeModals}>
        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="delete-title" onclick={(e) => e.stopPropagation()}>
            <h3 id="delete-title" class="modal-title">Delete Video</h3>
            <p class="modal-warning">Are you sure you want to delete "{selectedVideoName}"?</p>
            <p class="modal-warning-sub">This will permanently delete the video, transcripts, and all associated data.</p>
            <div class="modal-actions">
                <button class="modal-cancel" onclick={closeModals} disabled={isProcessing}>Cancel</button>
                <button class="modal-delete" onclick={handleDelete} disabled={isProcessing}>
                    {isProcessing ? 'Deleting...' : 'Delete'}
                </button>
            </div>
        </div>
    </div>
{/if}

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

    .success-content {
        flex: 1;
    }

    .done-button {
        background-color: var(--color-success);
        color: white;
        border: none;
        padding: var(--spacing-sm) var(--spacing-lg);
        border-radius: var(--radius-md);
        font-weight: var(--font-weight-semibold);
        cursor: pointer;
        transition: all var(--transition-fast);
        white-space: nowrap;
    }

    .done-button:hover {
        background-color: #45a049;
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
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

    .video-table-wrapper {
        background-color: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        overflow: hidden;
    }

    .video-table {
        width: 100%;
        border-collapse: collapse;
    }

    .video-table thead {
        background-color: var(--color-surface);
        border-bottom: 1px solid var(--color-border);
    }

    .video-table th {
        padding: var(--spacing-md) var(--spacing-lg);
        text-align: left;
        font-size: var(--font-size-sm);
        font-weight: var(--font-weight-semibold);
        color: var(--color-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .video-table tbody tr {
        border-bottom: 1px solid var(--color-border);
        transition: background-color var(--transition-fast);
    }

    .video-table tbody tr:last-child {
        border-bottom: none;
    }

    .video-table tbody tr:hover {
        background-color: var(--color-surface);
    }

    .video-table td {
        padding: var(--spacing-md) var(--spacing-lg);
        font-size: var(--font-size-sm);
        color: var(--color-text);
    }

    .video-name-cell {
        font-weight: var(--font-weight-medium);
        max-width: 300px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .action-cell {
        white-space: nowrap;
    }

    .edit-button {
        display: inline-block;
        padding: var(--spacing-xs) var(--spacing-md);
        background-color: var(--color-accent);
        color: var(--color-primary);
        border: 1px solid var(--color-accent);
        border-radius: var(--radius-md);
        font-size: var(--font-size-xs);
        font-weight: var(--font-weight-semibold);
        text-decoration: none;
        transition: all var(--transition-fast);
    }

    .edit-button:hover {
        background-color: var(--color-accent-hover);
        border-color: var(--color-accent-hover);
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
    }

    .rename-button,
    .delete-button {
        display: inline-block;
        padding: var(--spacing-xs) var(--spacing-md);
        border-radius: var(--radius-md);
        font-size: var(--font-size-xs);
        font-weight: var(--font-weight-semibold);
        cursor: pointer;
        transition: all var(--transition-fast);
        margin-left: var(--spacing-xs);
    }

    .rename-button {
        background-color: transparent;
        color: var(--color-text-secondary);
        border: 1px solid var(--color-border);
    }

    .rename-button:hover {
        background-color: var(--color-surface);
        border-color: var(--color-text-secondary);
    }

    .delete-button {
        background-color: transparent;
        color: var(--color-error);
        border: 1px solid var(--color-error);
    }

    .delete-button:hover {
        background-color: rgba(244, 67, 54, 0.1);
    }

    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: var(--z-modal, 1000);
    }

    .modal {
        background-color: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: var(--spacing-xl);
        min-width: 400px;
        max-width: 90vw;
    }

    .modal-title {
        margin: 0 0 var(--spacing-md) 0;
        font-size: var(--font-size-xl);
    }

    .modal-subtitle {
        color: var(--color-text-secondary);
        margin-bottom: var(--spacing-md);
    }

    .modal-warning {
        color: var(--color-error);
        font-weight: var(--font-weight-medium);
        margin-bottom: var(--spacing-sm);
    }

    .modal-warning-sub {
        color: var(--color-text-secondary);
        font-size: var(--font-size-sm);
        margin-bottom: var(--spacing-lg);
    }

    .modal-input {
        width: 100%;
        padding: var(--spacing-sm) var(--spacing-md);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        background-color: var(--color-surface);
        color: var(--color-text);
        font-size: var(--font-size-base);
        margin-bottom: var(--spacing-lg);
    }

    .modal-input:focus {
        outline: none;
        border-color: var(--color-accent);
    }

    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: var(--spacing-md);
    }

    .modal-cancel {
        background-color: transparent;
        color: var(--color-text-secondary);
        border: 1px solid var(--color-border);
        padding: var(--spacing-sm) var(--spacing-lg);
        border-radius: var(--radius-md);
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .modal-cancel:hover:not(:disabled) {
        background-color: var(--color-surface);
    }

    .modal-confirm {
        background-color: var(--color-accent);
        color: var(--color-primary);
        border: none;
        padding: var(--spacing-sm) var(--spacing-lg);
        border-radius: var(--radius-md);
        cursor: pointer;
        font-weight: var(--font-weight-semibold);
        transition: all var(--transition-fast);
    }

    .modal-confirm:hover:not(:disabled) {
        background-color: var(--color-accent-hover);
    }

    .modal-delete {
        background-color: var(--color-error);
        color: white;
        border: none;
        padding: var(--spacing-sm) var(--spacing-lg);
        border-radius: var(--radius-md);
        cursor: pointer;
        font-weight: var(--font-weight-semibold);
        transition: all var(--transition-fast);
    }

    .modal-delete:hover:not(:disabled) {
        background-color: #d32f2f;
    }

    .modal-cancel:disabled,
    .modal-confirm:disabled,
    .modal-delete:disabled {
        opacity: 0.6;
        cursor: not-allowed;
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

        .video-table-wrapper {
            overflow-x: auto;
        }

        .video-table {
            font-size: var(--font-size-xs);
        }

        .video-table th,
        .video-table td {
            padding: var(--spacing-sm) var(--spacing-md);
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

        .video-name-cell {
            max-width: 150px;
        }
    }
</style>
