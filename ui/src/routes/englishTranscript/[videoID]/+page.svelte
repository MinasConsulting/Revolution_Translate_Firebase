<script>
	import { page } from '$app/stores';
	import { saveChange, saveRead, transcriptClass } from "../../../utils/fire.js"
	import { onDestroy, onMount, tick } from 'svelte';
	import videojs from 'video.js';
	import 'video.js/dist/video-js.css'; // Import Video.js CSS
    import { englishTranscript, spanishTranscript } from '../../../utils/stores.js';

	let videoID = $page.params.videoID;
    let videoName = null;
	let player;
	let tsClass = new transcriptClass(videoID)
	let intervalId = null;
	let englishVis = true;
	let spanishVis = true;
	let videoLink = null;
    let translateLock = false;
    let rewindSec = 10;
    let fontSize = 16;
    let centerFactor = 5;
    let globalLock = false;
    let isEditing = false;
    let saveReadinProgress = false;

    let downloadButtonText = 'Download Video'
    let downloadButtonDisabled = false;

    const yellowColor = "#fcf756"
    const blueColor = "darkturquoise"

    onMount(async () => {

        englishTranscript.set([])
        spanishTranscript.set([])

        const loadingSpinner = document.querySelector('.loading-spinner');
        loadingSpinner.style.display = 'flex';

        const getLogin = async () => {
            let authenticated = localStorage.getItem('authenticated')
            if (!authenticated) {
                // // Redirect the user to the login page if not authenticated
                // authenticated = localStorage.getItem('authenticated') === 'true';
                window.location.href = '/login';
            }
        }
        const fetchTranscriptAndInitPlayer = async () => {
            await tsClass.init();

            if ($spanishTranscript.length>0) {
                translateLock = true;
                if ($englishTranscript.length !== $spanishTranscript.length){
                    alert("Transcript sync error. Editing disabled. Please reach out to Evan Stoelzel.")
                }
            }
            videoLink = tsClass.videoURL;


            // Initialize Video.js player after fetching the video URL
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

        loadingSpinner.style.display = 'none';
    });

  onDestroy(() => {
		clearInterval(intervalId);
		if (player) player.dispose(); // Dispose of the player instance
	});

  function resetShading() {
    const transcriptBox = document.querySelector('.transcript-box');
    for (var i = 0; i < $englishTranscript.length; i++) {
        const transcriptLineElement = transcriptBox.querySelector(`li[data-start-sec="${$englishTranscript[i].startSec}"]`); 
        transcriptLineElement.style.backgroundColor = "transparent"
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
			const transcriptLineElement = transcriptBox.querySelector(`li[data-start-sec="${transcriptLine.startSec}"]`); // Select transcript line element
			const scrollLineElement = transcriptBox.querySelector(`li[data-start-sec="${scrollLine.startSec}"]`); // Select transcript line element
            const prevLineElement = transcriptBox.querySelector(`li[data-start-sec="${prevLine.startSec}"]`); // Select transcript line element

			if (transcriptLineElement) {
				// Apply highlighting to the current line
                if (prevLineElement && prevLineElement.style.backgroundColor == blueColor){
                        prevLineElement.style.backgroundColor = yellowColor
                    }
                

				transcriptLineElement.style.backgroundColor = blueColor;

				const transcriptBox = document.querySelector('.transcript-box');
				const scrollTop = transcriptBox.scrollTop; // Current scroll position
				const targetTop = scrollLineElement.offsetTop; // Top position of the target element
				const scrollDistance = Math.abs(targetTop - scrollTop); // Distance to scroll
                
                if (!transcriptLine.lineRead && !saveReadinProgress){
                    // if spanish transcript is present do a save on that document.
                    saveReadinProgress = true
                    saveRead(transcriptLine,videoID)
                    $englishTranscript[scriptIndex].lineRead = true
                    saveReadinProgress = false
                }

                // transcriptLine.dataset.lineread = true

				if (scrollDistance > 500){
					scrollLineElement.scrollIntoView({
					behavior: 'auto'
					}) // Scroll to the line
				}
				else {
					scrollLineElement.scrollIntoView({
					behavior: 'smooth'
					}) // Scroll to the line
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
	// Set the span to editable on double click
	event.target.contentEditable = "true";
	// Optional: Focus the element automatically
	event.target.focus();

	// Add a listener for blur event to capture changes and reset editability
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
	// Perform necessary actions like saving changes
	// ...
    await tick();
	// Remove blur listener after handling the edit
	event.target.removeEventListener('blur', handleEditComplete);
    globalLock = false;
    isEditing = false;
	}

    function handleVisChange(event) {
        const selectedOption = event.target.value;
        // Set boolean values based on selected option
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
		console.log(englishVis)
		console.log(spanishVis)
    }

    async function handleTranslateClick() {
        if ($spanishTranscript.length===0) {
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

            // Create a blob object with the text content
        const blob = new Blob([exportText], { type: "text/plain" });

        // Create a download link with the filename "transcript.txt"
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${videoSplit}_English_Transcript.csv`;
        link.click();

        if ($spanishTranscript.length === $englishTranscript.length) {
            let exportText = "Start Time, Text\n"

            $spanishTranscript.forEach((line) => {
                exportText += `"${line.startTime}","${line.text}"\n`
            })

            // Create a blob object with the text content
            const blob = new Blob([exportText], { type: "text/plain" });

            // Create a download link with the filename "transcript.txt"
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


</script>

<h1>Transcript for {videoName}</h1>
<div class="loading-spinner">
    <div class="spinner"></div>
</div>

<menu>
	<button on:click={handleTranslateClick} class:disabled={translateLock}>Translate</button>
    <button on:click={exportScriptClick} class:disabled={globalLock}>Export Script</button>
    <button on:click={() => handleDownload(videoName)} class:disabled={globalLock||downloadButtonDisabled}>{downloadButtonText}</button>
    <button style="float:right" on:click={e => fontSize++}>Increase font size</button>
    <button style="float:right; margin-right:5px" on:click={e => fontSize--}>Decrease font size</button>
    <button style="float:right; margin-right:5px;" on:click={resetShading}>Reset Shading</button>
    <select id="centerFactor" style="float:right; margin-right: 5px" bind:value={centerFactor}>
        {#each [...Array(9).keys()] as i}
          <option value={i}>{i}</option>
        {/each}
      </select>
    <label for="centerFactor" style="float:right; margin-right:5px">Scroll buffer:</label>
    {#if $spanishTranscript.length > 0}
        <label for="textView">Choose a view:</label>
        <select name="textView" id="textView" on:change={handleVisChange}>
            <option value="Combined">Combined</option>
            <option value="English Only">English Only</option>
            <option value="Spanish Only">Spanish Only</option>
        </select>
    {/if}

</menu>


<div class="video-container">
	<video id="my-video" class="video-js" controls preload="auto" style="width:100%; height:75vh;"></video>
    <button style= "float:right" on:click={rewindClick}>Rewind</button>
    <select style="float:right; margin-right: 5px" bind:value={rewindSec}>
        {#each [2,5,7,10,12,15] as i}
          <option value={i}>{i}</option>
        {/each}
      </select>
      
</div>

<div class="transcript-box" >
    {#if isEditing}
    <div class="loading-spinner ">
        <div class="spinner"></div>
    </div>
    {/if}
    {#if $englishTranscript.length > 0}
        <ul>
            {#each $englishTranscript as line, index}
                <li data-start-sec={line.startSec} style="list-style: none"> 
                    <div class="time-and-text">
                        <div class="startTime-box" style="background-color: {line.lineRead ? yellowColor : 'transparent'};">{line.startTime}</div>  
                        <div class="text-container">
                            {#if englishVis}
                                <div data-placeholder="Insert text..." style="font-size: {fontSize}px" class="english-line" contentEditable="false" on:dblclick={handleDoubleClick} data-docID={line.docID} data-start-sec={line.startSec} data-end-sec={line.endSec} data-language="englishTranscript" data-is-placeholder={!line.text} data-line-read={line.lineRead}> 
                                    {line.text}
                                </div>
                            {/if}
                            {#if spanishVis && $spanishTranscript.length > 0 && $spanishTranscript.length === $englishTranscript.length}
                                <div data-placeholder="Insert text..." style="font-size: {fontSize}px" class="spanish-line" contentEditable="false" on:dblclick={handleDoubleClick} data-docID={$spanishTranscript[index].docID} data-start-sec={$spanishTranscript[index].startSec} data-end-sec={$spanishTranscript[index].endSec} data-language="spanishTranscript" data-is-placeholder={!$spanishTranscript[index].text} data-line-read={$spanishTranscript[index].lineRead}> 
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

<style>
    .startTime-box {
        box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.15);
        padding: 5px;
        border-radius: 5px;
        margin-right: 10px;
        display: inline-block;
    }
    .transcript-box {
        width: 60%;
        height: 75vh;
        overflow-y: scroll;
        border: 1px solid #ccc;
        float: right;
        position: relative;
    }
    .video-container {
        float: left;
        width: 35%;
        max-height: 75vh;
    }
    .time-and-text {
        display: flex;
        align-items: flex-start;
    }
    .text-container {
        display: flex;
        flex-direction: column; /* Stack spans vertically */
		border: 1px solid black; /* Add thin black border */
        padding: 5px; /* Add padding for spacing */
		flex-grow: 1; /* Allow container to grow to fill remaining space */
    }
    .english-line,
    .spanish-line {
        display: block;
        margin-top: 5px; /* Adjust margin between lines */
    }
    .spanish-line {
        font-family: Arial, sans-serif; /* Set font family for Spanish lines */
        font-weight: bold; /* Set font weight to bold for a blockier style */
    }
    .disabled {
    background-color: #ccc; /* Grey out the button */
    color: #999; /* Optionally change text color */
    cursor: not-allowed; /* Optionally change cursor */
  }
  .loading-spinner {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 10000000px;
    overflow: visible;
    background-color: rgba(255, 255, 255, 0.7); /* Semi-transparent overlay */
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999; /* Ensure the spinner is on top of other elements */
}
.spinner {
  border: 5px solid rgba(0, 0, 0, 0.2);
  border-top-color: #fff; /* White color for the spinning element */
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
}


@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

[data-placeholder]:empty:before {
     content: attr(data-placeholder);
     color: #888;
     font-style: italic;
}
</style>

