<script>
	import { page } from '$app/stores';
	import { saveChange, saveRead, transcriptClass } from "../../../utils/fire.js"
	import { onDestroy, onMount, tick } from 'svelte';
	import videojs from 'video.js';
	import 'video.js/dist/video-js.css';
    import { englishTranscript, spanishTranscript } from '../../../utils/stores.js';

	let videoID = $page.params.videoID;
    let videoName = $state(null);
	let player;
	let tsClass = new transcriptClass(videoID)
	let intervalId = null;
	let englishVis = $state(true);
	let spanishVis = $state(true);
	let videoLink = $state(null);
    let translateLock = $state(false);
    let rewindSec = $state(10);
    let fontSize = $state(16);
    let centerFactor = $state(5);
    let globalLock = $state(false);
    let isEditing = $state(false);
    let saveReadinProgress = false;

    let downloadButtonText = $state('Download Video');
    let downloadButtonDisabled = $state(false);

    const yellowColor = "#fcf756"
    const blueColor = "#7b9bd8"

    onMount(async () => {
        englishTranscript.set([])
        spanishTranscript.set([])

        const loadingSpinner = document.querySelector('.loading-spinner');
        if (loadingSpinner) loadingSpinner.style.display = 'flex';

        const getLogin = async () => {
            let authenticated = localStorage.getItem('authenticated')
            if (!authenticated) {
                window.location.href = '/login';
            }
        }
        
        const fetchTranscriptAndInitPlayer = async () => {
            await tsClass.init();

            if (tsClass.videoData.translateInProgress == true){
                translateLock = true;
            }
            else if ($spanishTranscript.length>0) {
                translateLock = true;
                if ($englishTranscript.length !== $spanishTranscript.length){
                    alert("Transcript sync error. Editing disabled. Please reach out to Evan Stoelzel.")
                }
            }
            videoLink = tsClass.videoURL;

            player = videojs(document.getElementById('my-video'), {
                controls: true,
                fluid: false,
                preload: 'auto',
                sources: [{
                    src: videoLink,
                    type: 'video/mp4'
                }],
                playbackRates: [0.35, 0.5, 0.75, 0.8, 0.85, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1, 1.25, 1.5, 1.75, 2]
            });

            if ($englishTranscript.length === $spanishTranscript.length){
                player.playbackRate(0.9)
            }
        }

		const pollingInterval = 100;
        intervalId = setInterval(getPlaybackPosition, pollingInterval);
        await getLogin()
        if (localStorage.getItem('videoName') == null) {
            window.location.href = '/';
        }
        else {
            videoName = localStorage.getItem('videoName')
        }

        await fetchTranscriptAndInitPlayer();

        if (loadingSpinner) loadingSpinner.style.display = 'none';
    });

  onDestroy(() => {
		clearInterval(intervalId);
		if (player) player.dispose();
	});

  function resetShading() {
    const transcriptBox = document.querySelector('.transcript-box');
    if (!transcriptBox) return;
    for (var i = 0; i < $englishTranscript.length; i++) {
        const transcriptLineElement = transcriptBox.querySelector(`li[data-start-sec="${$englishTranscript[i].startSec}"]`); 
        if (transcriptLineElement) transcriptLineElement.style.backgroundColor = "transparent"
	}
  }

  function getPlaybackPosition() {
	if (player && player.currentTime() > 0 && !player.paused()) {
    const currentPosition = player.currentTime();
	let transcriptLine = null
	let scrollLine = null
    let prevLine = null
    let scriptIndex = null
	
	for (var i = 0; i < $englishTranscript.length; i++) {
		if (currentPosition >= $englishTranscript[i].startSec && currentPosition < $englishTranscript[i].endSec){
            transcriptLine = $englishTranscript[i]
            scriptIndex = i
            if (i > 0) {
                prevLine = $englishTranscript[i-1]
            }
            else {
                prevLine = $englishTranscript[0]
            }
			if (i < centerFactor) {
				scrollLine = $englishTranscript[0]
			}
			else {
				scrollLine = $englishTranscript[i-centerFactor]
			}
			break;
		}
	}

    if (transcriptLine) {
        const transcriptBox = document.querySelector('.transcript-box');
		if (transcriptBox) {
			const transcriptLineElement = transcriptBox.querySelector(`li[data-start-sec="${transcriptLine.startSec}"]`);
			const scrollLineElement = transcriptBox.querySelector(`li[data-start-sec="${scrollLine.startSec}"]`);
            const prevLineElement = transcriptBox.querySelector(`li[data-start-sec="${prevLine.startSec}"]`);

			if (transcriptLineElement) {
                if (prevLineElement && prevLineElement.style.backgroundColor == blueColor){
                    prevLineElement.style.backgroundColor = yellowColor
                }

				transcriptLineElement.style.backgroundColor = blueColor;

				// Pixel-based centering: scroll so current line is vertically centered
				const targetScrollTop = transcriptLineElement.offsetTop - (transcriptBox.clientHeight / 2 - transcriptLineElement.clientHeight / 2);
				const scrollDistance = Math.abs(targetScrollTop - transcriptBox.scrollTop);
                
                if (!transcriptLine.lineRead && !saveReadinProgress){
                    saveReadinProgress = true
                    saveRead(transcriptLine,videoID,"englishTranscript")
                    $englishTranscript[scriptIndex].lineRead = true
                    saveReadinProgress = false
                }

                if ($spanishTranscript.length === $englishTranscript.length && !$spanishTranscript[scriptIndex].lineRead && !saveReadinProgress){
                    saveReadinProgress = true
                    saveRead($spanishTranscript[scriptIndex],videoID,"spanishTranscript")
                    $spanishTranscript[scriptIndex].lineRead = true
                    saveReadinProgress = false
                }

				// Only scroll if we're more than a small threshold away from target
				if (scrollDistance > 40){
					transcriptBox.scrollTo({ 
						top: targetScrollTop, 
						behavior: scrollDistance > 500 ? 'auto' : 'smooth' 
					});
				}
			}
		}
    }
}
  }

  function handleDoubleClick(event) {
    if((translateLock && event.target.dataset.language === "englishTranscript") || globalLock) {return}

    globalLock = true;

	player.pause();
	event.target.contentEditable = "true";
	event.target.focus();

	event.target.addEventListener('blur', handleEditComplete);
	}

async function handleEditComplete(event) {
    const startSec = parseFloat(event.target.dataset.startSec) 
    const endSec = parseFloat(event.target.dataset.endSec)

    event.target.contentEditable = "false"

    player.currentTime(startSec)
	player.play();

	const newDocID = await saveChange(event,videoID)
    console.log(newDocID)

    const playPosition = startSec + (endSec-startSec)*newDocID.positionScale
    if(playPosition !== startSec){
        player.currentTime(playPosition)
        player.play();
    }

    if(newDocID.refresh) {
        isEditing = true;
        await tsClass.refreshTranscript()
        console.log("transcript refreshed")
    }
    event.target.textContent = event.target.textContent

    await tick();
	event.target.removeEventListener('blur', handleEditComplete);
    globalLock = false;
    isEditing = false;
	}

    function handleVisChange(event) {
        const selectedOption = event.target.value;
        if (selectedOption === 'English Only') {
            englishVis = true;
            spanishVis = false;
        } else if (selectedOption === 'Spanish Only') {
            englishVis = false;
            spanishVis = true;
        } else if (selectedOption === 'Combined') {
            englishVis = true;
            spanishVis = true;
        }
    }

    async function handleTranslateClick() {
        if ($spanishTranscript.length===0 && !translateLock) {
            const confirmation = window.confirm('Are you sure? All English edits must be complete before proceeding with AI translation.');
            if (confirmation) {
                translateLock = true
                await tsClass.spanishTranslate();
            }
        } 
    }

    function rewindClick () {
        player.currentTime(player.currentTime() - rewindSec);
    }

    function exportScriptClick () {
        const videoSplit = videoName.split(".")[0]

        let exportText = "Start Time, Text\n"

        $englishTranscript.forEach((line) => {
            exportText += `"${line.startTime}","${line.text}"\n`
        })

        const blob = new Blob([exportText], { type: "text/plain" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${videoSplit}_English_Transcript.csv`;
        link.click();

        if ($spanishTranscript.length === $englishTranscript.length) {
            let exportText = "Start Time, Text\n"

            $spanishTranscript.forEach((line) => {
                exportText += `"${line.startTime}","${line.text}"\n`
            })

            const blob = new Blob([exportText], { type: "text/plain" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = `${videoSplit}_Spanish_Transcript.csv`;
            link.click();
        }
    }

    async function handleDownload(videoName) {
        downloadButtonText = 'Download in progress...';
        downloadButtonDisabled = true;
        
        await tsClass.downloadVideo(videoName);

        downloadButtonText = 'Download Video';
        downloadButtonDisabled = false;
    }

    function handleBackClick() {
        window.location.href = '/';
    }
</script>

<svelte:head>
    <title>{videoName || 'Loading...'} - Revolution Translate</title>
</svelte:head>

<div class="page-container">
    <div class="loading-spinner" style="display: none;">
        <div class="spinner"></div>
    </div>

    <header class="editor-header">
        <div class="header-left">
            <button onclick={handleBackClick} class="back-button">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="19" y1="12" x2="5" y2="12"></line>
                    <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                Back
            </button>
            <h1 class="video-title">{videoName || 'Loading...'}</h1>
        </div>
    </header>

    <div class="toolbar">
        <div class="toolbar-section">
            <button onclick={handleTranslateClick} class:disabled={translateLock} class="primary">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 8h14M9 21h6m-7-4 4.5-9 4.5 9M2 3h20"></path>
                </svg>
                Translate
            </button>
            <button onclick={exportScriptClick} class:disabled={globalLock}>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Export
            </button>
            <button onclick={() => handleDownload(videoName)} class:disabled={globalLock||downloadButtonDisabled}>
                {downloadButtonText}
            </button>
        </div>

        <div class="toolbar-section">
            {#if $spanishTranscript.length > 0}
                <select id="textView" onchange={handleVisChange} class="view-select">
                    <option value="Combined">Combined</option>
                    <option value="English Only">English Only</option>
                    <option value="Spanish Only">Spanish Only</option>
                </select>
            {/if}
        </div>

        <div class="toolbar-section">
            <button onclick={resetShading} title="Reset line highlighting">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                    <path d="M21 3v5h-5"></path>
                    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                    <path d="M3 21v-5h5"></path>
                </svg>
            </button>
            <div class="control-group">
                <label for="centerFactor" class="control-label">Buffer</label>
                <select id="centerFactor" bind:value={centerFactor}>
                    {#each [...Array(9).keys()] as i}
                        <option value={i}>{i}</option>
                    {/each}
                </select>
            </div>
            <div class="control-group">
                <button onclick={() => fontSize--} title="Decrease font size">A-</button>
                <button onclick={() => fontSize++} title="Increase font size">A+</button>
            </div>
        </div>
    </div>

    <div class="editor-content">
        <div class="video-section">
            <div class="video-wrapper">
                <video id="my-video" class="video-js" controls preload="auto"></video>
            </div>
            <div class="video-controls">
                <select bind:value={rewindSec} class="rewind-select">
                    {#each [2,5,7,10,12,15] as i}
                        <option value={i}>{i}s</option>
                    {/each}
                </select>
                <button onclick={rewindClick} class="rewind-button">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="11 19 2 12 11 5 11 19"></polygon>
                        <polygon points="22 19 13 12 22 5 22 19"></polygon>
                    </svg>
                    Rewind
                </button>
            </div>
        </div>

        <div class="transcript-section">
            {#if isEditing}
                <div class="loading-spinner">
                    <div class="spinner"></div>
                </div>
            {/if}
            
            <div class="transcript-box">
                {#if $englishTranscript.length > 0}
                    <ul class="transcript-list">
                        {#each $englishTranscript as line, index}
                            <li data-start-sec={line.startSec} class="transcript-item"> 
                                <div class="transcript-line">
                                    <div class="time-indicators"> 
                                        {#if englishVis}
                                            <div class="time-badge" class:read={line.lineRead}>
                                                {line.startTime}
                                            </div>
                                        {/if}
                                        {#if spanishVis && englishVis && $spanishTranscript.length > 0 && $spanishTranscript.length === $englishTranscript.length}
                                            <div class="time-badge spacer" class:read={$spanishTranscript[index].lineRead}></div>
                                        {/if}
                                        {#if spanishVis && !englishVis && $spanishTranscript.length > 0 && $spanishTranscript.length === $englishTranscript.length}
                                            <div class="time-badge" class:read={$spanishTranscript[index].lineRead}>
                                                {line.startTime}
                                            </div>
                                        {/if}
                                    </div>
                                    <div class="text-content">
                                        {#if englishVis}
                                            <div 
                                                data-placeholder="Insert text..." 
                                                class="editable-text english" 
                                                class:editable={!translateLock}
                                                contentEditable="false" 
                                                ondblclick={handleDoubleClick} 
                                                data-docID={line.docID} 
                                                data-start-sec={line.startSec} 
                                                data-end-sec={line.endSec} 
                                                data-language="englishTranscript" 
                                                data-is-placeholder={!line.text} 
                                                style="font-size: {fontSize}px"> 
                                                {line.text}
                                            </div>
                                        {/if}
                                        {#if spanishVis && $spanishTranscript.length > 0 && $spanishTranscript.length === $englishTranscript.length}
                                            <div 
                                                data-placeholder="Insert text..." 
                                                class="editable-text spanish" 
                                                class:editable={true}
                                                contentEditable="false" 
                                                ondblclick={handleDoubleClick} 
                                                data-docID={$spanishTranscript[index].docID} 
                                                data-start-sec={$spanishTranscript[index].startSec} 
                                                data-end-sec={$spanishTranscript[index].endSec} 
                                                data-language="spanishTranscript" 
                                                data-is-placeholder={!$spanishTranscript[index].text} 
                                                style="font-size: {fontSize}px"> 
                                                {$spanishTranscript[index].text}
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                            </li>
                        {/each}
                    </ul>
                {/if}
            </div>
        </div>
    </div>
</div>

<style>
    .page-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        background-color: var(--color-primary);
    }

    .editor-header {
        background-color: var(--color-surface-elevated);
        border-bottom: 1px solid var(--color-border);
        padding: var(--spacing-lg) var(--spacing-xl);
        box-shadow: var(--shadow-sm);
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: var(--spacing-lg);
        max-width: 1800px;
        margin: 0 auto;
    }

    .back-button {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm) var(--spacing-md);
        background-color: transparent;
        border: 1px solid var(--color-border);
    }

    .back-button:hover {
        background-color: var(--color-surface);
    }

    .video-title {
        font-size: var(--font-size-2xl);
        margin: 0;
        word-break: break-word;
    }

    .toolbar {
        background-color: var(--color-surface-elevated);
        border-bottom: 1px solid var(--color-border);
        padding: var(--spacing-md) var(--spacing-xl);
        display: flex;
        gap: var(--spacing-lg);
        align-items: center;
        flex-wrap: wrap;
        max-width: 1800px;
        margin: 0 auto;
        width: 100%;
    }

    .toolbar-section {
        display: flex;
        gap: var(--spacing-sm);
        align-items: center;
        flex-wrap: wrap;
    }

    .toolbar-section:first-child {
        flex: 1;
    }

    .toolbar button {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
    }

    .control-group {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        padding: var(--spacing-xs) var(--spacing-sm);
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
    }

    .control-label {
        font-size: var(--font-size-xs);
        color: var(--color-text-secondary);
        margin: 0;
    }

    .control-group select {
        padding: var(--spacing-xs);
        font-size: var(--font-size-sm);
        min-width: 50px;
    }

    .control-group button {
        padding: var(--spacing-xs) var(--spacing-sm);
        font-size: var(--font-size-sm);
        border: none;
        background-color: transparent;
    }

    .control-group button:hover {
        background-color: var(--color-border);
    }

    .view-select {
        padding: var(--spacing-sm) var(--spacing-md);
    }

    .editor-content {
        flex: 1;
        display: flex;
        gap: var(--spacing-lg);
        padding: var(--spacing-lg);
        max-width: 1800px;
        margin: 0 auto;
        width: 100%;
    }

    .video-section {
        flex: 0 0 40%;
        display: flex;
        flex-direction: column;
        gap: var(--spacing-md);
    }

    .video-wrapper {
        background-color: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }

    .video-wrapper :global(.video-js) {
        width: 100%;
        height: auto;
        aspect-ratio: 16 / 9;
    }

    .video-controls {
        display: flex;
        gap: var(--spacing-sm);
        align-items: center;
    }

    .rewind-select {
        width: auto;
        min-width: 70px;
    }

    .rewind-button {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        flex: 1;
    }

    .transcript-section {
        flex: 1;
        position: relative;
        background-color: var(--color-surface-elevated);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }

    .transcript-box {
        height: calc(100vh - 280px);
        overflow-y: auto;
        padding: var(--spacing-md);
    }

    .transcript-list {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
    }

    .transcript-item {
        list-style: none;
        transition: background-color var(--transition-base);
        border-radius: var(--radius-md);
        padding: var(--spacing-xs);
    }

    .transcript-line {
        display: flex;
        gap: var(--spacing-md);
        align-items: flex-start;
    }

    .time-indicators {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);
        flex-shrink: 0;
    }

    .time-badge {
        padding: var(--spacing-xs) var(--spacing-sm);
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-sm);
        font-size: var(--font-size-xs);
        font-family: var(--font-mono);
        color: var(--color-text-secondary);
        text-align: center;
        min-width: 90px;
        transition: all var(--transition-fast);
    }

    .time-badge.read {
        background-color: rgba(252, 247, 86, 0.15);
        border-color: var(--color-accent);
        color: var(--color-accent);
    }

    .time-badge.spacer {
        min-height: 24px;
        border-style: dashed;
    }

    .text-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        min-width: 0;
    }

    .editable-text {
        padding: var(--spacing-sm) var(--spacing-md);
        background-color: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        line-height: var(--line-height-relaxed);
        word-wrap: break-word;
        transition: all var(--transition-fast);
    }

    .editable-text.editable:hover {
        border-color: var(--color-accent);
        background-color: var(--color-primary-light);
        cursor: text;
    }

    .editable-text.spanish {
        font-weight: var(--font-weight-semibold);
        border-left: 3px solid var(--color-secondary);
    }

    .editable-text[contenteditable="true"] {
        outline: 2px solid var(--color-accent);
        background-color: var(--color-primary-light);
        box-shadow: var(--shadow-md);
    }

    [data-placeholder]:empty:before {
        content: attr(data-placeholder);
        color: var(--color-text-muted);
        font-style: italic;
    }

    @media (max-width: 1200px) {
        .editor-content {
            flex-direction: column;
        }

        .video-section {
            flex: 0 0 auto;
        }

        .transcript-box {
            height: 600px;
        }
    }

    @media (max-width: 768px) {
        .editor-header,
        .toolbar,
        .editor-content {
            padding-left: var(--spacing-md);
            padding-right: var(--spacing-md);
        }

        .video-title {
            font-size: var(--font-size-xl);
        }

        .toolbar {
            flex-direction: column;
            align-items: stretch;
        }

        .toolbar-section {
            width: 100%;
            justify-content: space-between;
        }

        .time-badge {
            min-width: 70px;
            font-size: 10px;
        }

        .transcript-box {
            height: 500px;
        }
    }
</style>
