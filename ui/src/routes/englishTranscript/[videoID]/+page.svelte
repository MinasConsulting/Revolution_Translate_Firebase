<script>
	import { page } from '$app/stores';
	import { saveChange, transcriptClass } from "../../../utils/fire.js"
	import { onDestroy, onMount } from 'svelte';
	import videojs from 'video.js';
	import 'video.js/dist/video-js.css'; // Import Video.js CSS

	let videoID = $page.params.videoID;
	let player;
	let tsClass = new transcriptClass(videoID)
	let transcript = null;
	let spanishTranscript = undefined;
	let intervalId = null;
	let englishVis = true;
	let spanishVis = true;
	let videoLink = null;

    onMount(async () => {
        const fetchTranscriptAndInitPlayer = async () => {
            await tsClass.init();
			transcript = tsClass.englishTranscript;
            spanishTranscript = tsClass.spanishTranscript;
            videoLink = tsClass.videoURL;

            // Initialize Video.js player after fetching the video URL
            player = videojs(document.getElementById('my-video'), {
                controls: true,
                fluid: true,
                preload: 'auto',
                sources: [{
                    src: videoLink,
                    type: 'video/mp4'
                }]
            });


        }

		const pollingInterval = 100;
        intervalId = setInterval(getPlaybackPosition, pollingInterval);

        await fetchTranscriptAndInitPlayer();
    });

  onDestroy(() => {
		clearInterval(intervalId);
		if (player) player.dispose(); // Dispose of the player instance
	});



  function getPlaybackPosition() {
	if (player && player.currentTime() > 0 && !player.paused()) {
    const currentPosition = player.currentTime();
	let transcriptLine = null
	let scrollLine = null
	const centerFactor = 5
	
	for (var i = 0; i < transcript.length; i++) {
		if (currentPosition >= transcript[i].startSec && currentPosition < transcript[i].endSec){
			transcriptLine = transcript[i]
			if (i < centerFactor) {
				scrollLine = transcript[i]
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

			if (transcriptLineElement) {
				// Apply highlighting to the current line
				transcriptLineElement.style.backgroundColor = 'yellow';

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
	console.log(event)
	// Set the span to editable on double click
	event.target.contentEditable = "true";
	// Optional: Focus the element automatically
	event.target.focus();

	// Add a listener for blur event to capture changes and reset editability
	event.target.addEventListener('blur', handleEditComplete);
	}

async function handleEditComplete(event) {
	player.currentTime(parseFloat(event.target.dataset.startSec))
	player.play();
	console.log(event)
	// Access the modified text
	const editedText = event.target.textContent;

	const newDocID = await saveChange(event,videoID)

	console.log("New Doc ID",newDocID)

	event.target.dataset.docid = newDocID

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
</script>

<h1>English Transcript for Video {videoID}</h1>
<menu>
	<button on:click={async () => {await tsClass.spanishTranslate(); spanishTranscript = tsClass.spanishTranscript;}}>Translate</button>
	<!-- <label for="textView">Choose a view:</label>
	<select name="textView" id="textView" on:change={handleVisChange}>
		<option value="English Only">English Only</option>
		<option value="Spanish Only">Spanish Only</option>
		<option value="Combined">Combined</option>
	</select> -->

</menu>


<div class="video-container">
	<video id="my-video" class="video-js" controls preload="auto" style="width:100%"></video>
</div>

<div class="transcript-box">
    {#if transcript}
        <ul>
            {#each transcript as line, index (line.startSec)}
                <li data-start-sec={line.startSec} style="list-style: none"> 
                    <div class="time-and-text">
                        <div class="startTime-box">{line.startTime}</div> 
                        <div class="text-container">
                            {#if englishVis}
                                <div class="english-line" contentEditable="false" on:dblclick={handleDoubleClick} data-docID={line.docID} data-start-sec={line.startSec} data-language="englishTranscript"> 
                                    {line.text}
                                </div>
                            {/if}
                            {#if spanishVis && spanishTranscript}
                                <div class="spanish-line" contentEditable="false" on:dblclick={handleDoubleClick} data-docID={spanishTranscript[index].docID} data-start-sec={spanishTranscript[index].startSec} data-language="spanishTranscript"> 
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
    .video-container {
        display: flex; /* Use flexbox */
        justify-content: center; /* Center items horizontally */
        align-items: center; /* Center items vertically */
        width: 35%;
       /* height: 100vh;  Use 100% of the viewport height */
    }
</style>

