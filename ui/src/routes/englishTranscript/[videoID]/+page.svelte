<script>
	import { page } from '$app/stores';
	import { saveChange, transcriptClass } from "../../../utils/fire.js"
	import { onDestroy, onMount } from 'svelte';
	import videojs from 'video.js';
	import 'video.js/dist/video-js.css'; // Import Video.js CSS

	let videoID = $page.params.videoID;
    let videoName = null;
	let player;
	let tsClass = new transcriptClass(videoID)
	let transcript = null;
	let spanishTranscript = undefined;
	let intervalId = null;
	let englishVis = true;
	let spanishVis = true;
	let videoLink = null;
    let translateLock = false;
    let rewindSec = 10;
    let fontSize = 16;
    let centerFactor = 5;

    const yellowColor = "#fcf756"
    const blueColor = "darkturquoise"

    onMount(async () => {

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
			transcript = tsClass.englishTranscript;
            spanishTranscript = tsClass.spanishTranscript;
            if (spanishTranscript) {
                translateLock = true;
            }
            videoLink = tsClass.videoURL;

            // Initialize Video.js player after fetching the video URL
            player = videojs(document.getElementById('my-video'), {
                controls: true,
                fluid: true,
                preload: 'auto',
                sources: [{
                    src: videoLink,
                    type: 'video/mp4'
                }],
                playbackRates: [0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.25, 1.5, 1.75, 2]
            });


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
    for (var i = 0; i < transcript.length; i++) {
        const transcriptLineElement = transcriptBox.querySelector(`li[data-start-sec="${transcript[i].startSec}"]`); 
        transcriptLineElement.style.backgroundColor = "transparent"
	}

  }

  function getPlaybackPosition() {
	if (player && player.currentTime() > 0 && !player.paused()) {
    const currentPosition = player.currentTime();
	let transcriptLine = null
	let scrollLine = null
    let prevLine = null
	
	for (var i = 0; i < transcript.length; i++) {
		if (currentPosition >= transcript[i].startSec && currentPosition < transcript[i].endSec){
            transcriptLine = transcript[i]
            if (i > 0) {
                prevLine = transcript[i-1]
            }
            else {
                prevLine = transcript[0]
            }
			if (i < centerFactor) {
				scrollLine = transcript[0]
			}
			else {
				scrollLine = transcript[i-centerFactor]
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

    player.currentTime(startSec)
	player.play();

	const newDocID = await saveChange(event,videoID)
    console.log(newDocID)

	event.target.dataset.docid = newDocID.docID

    const playPosition = startSec + (endSec-startSec)*newDocID.positionScale
    if(playPosition !== startSec){
        player.currentTime(playPosition)
        player.play();
    }

	// Perform necessary actions like saving changes
	// ...

	// Reset contentEditable to false after editing
	event.target.contentEditable = "false";
	// Remove blur listener after handling the edit
	event.target.removeEventListener('blur', handleEditComplete);
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
        if (spanishTranscript == undefined) {
            const confirmation = window.confirm('Are you sure? All English edits must be complete before proceeding with AI translation.');
            if (confirmation) {
                translateLock = true
                await tsClass.spanishTranslate();
                spanishTranscript = tsClass.spanishTranscript;
            }
        } 
    }

    function rewindClick () {
        player.currentTime(player.currentTime() - rewindSec);
    }
</script>

<h1>Transcript for {videoName}</h1>
<div class="loading-spinner">
    <div class="spinner"></div>
</div>

<menu>
	<button on:click={handleTranslateClick} class:disabled={translateLock}>Translate</button>
    <button style="float:right" on:click={e => fontSize++}>Increase font size</button>
    <button style="float:right; margin-right:5px" on:click={e => fontSize--}>Decrease font size</button>
    <button style="float:right; margin-right:5px;" on:click={resetShading}>Reset Shading</button>
    <select id="centerFactor" style="float:right; margin-right: 5px" bind:value={centerFactor}>
        {#each [...Array(9).keys()] as i}
          <option value={i}>{i}</option>
        {/each}
      </select>
    <label for="centerFactor" style="float:right; margin-right:5px">Scroll buffer:</label>
	<!-- <label for="textView">Choose a view:</label>
	<select name="textView" id="textView" on:change={handleVisChange}>
		<option value="English Only">English Only</option>
		<option value="Spanish Only">Spanish Only</option>
		<option value="Combined">Combined</option>
	</select> -->

</menu>


<div class="video-container">
	<video id="my-video" class="video-js" controls preload="auto" style="width:100%"></video>
    <button style= "float:right" on:click={rewindClick}>Rewind</button>
    <select style="float:right; margin-right: 5px" bind:value={rewindSec}>
        {#each [2,5,7,10,12,15] as i}
          <option value={i}>{i}</option>
        {/each}
      </select>
      
</div>

<div class="transcript-box">
    {#if transcript}
        <ul>
            {#each transcript as line, index}
                <li data-start-sec={line.startSec} style="list-style: none"> 
                    <div class="time-and-text">
                        <div class="startTime-box">{line.startTime}</div> 
                        <div class="text-container">
                            {#if englishVis}
                                <div style="font-size: {fontSize}px" class="english-line" contentEditable="false" on:dblclick={handleDoubleClick} data-docID={line.docID} data-start-sec={line.startSec} data-end-sec={line.endSec} data-language="englishTranscript"> 
                                    {line.text}
                                </div>
                            {/if}
                            {#if spanishVis && spanishTranscript}
                                <div style="font-size: {fontSize}px" class="spanish-line" contentEditable="false" on:dblclick={handleDoubleClick} data-docID={spanishTranscript[index].docID} data-start-sec={spanishTranscript[index].startSec} data-end-sec={spanishTranscript[index].endSec} data-language="spanishTranscript"> 
                                    {spanishTranscript[index].text}
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
        height: 700px;
        overflow-y: scroll;
        border: 1px solid #ccc;
        float: right;
    }
    .video-container {
        float: left;
        width: 35%;
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
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent overlay */
  z-index: 999; /* Ensure the spinner is on top of other elements */
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
</style>

