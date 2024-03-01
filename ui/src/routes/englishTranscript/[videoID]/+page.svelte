<script>
	import { page } from '$app/stores';
	import { getTranscript, saveChange } from "../../../utils/fire.js"
	import { onDestroy, onMount } from 'svelte';


	let videoID = $page.params.videoID;
	let player;
	let transcript = null;
	let intervalId = null;

	const fetchTranscript = async () => {
		transcript = await getTranscript(videoID)
	}

	fetchTranscript()

	onMount(() => {
	if (window.YT) {
		player = new YT.Player('player', {
        height: '700',
        width: '100%', // Adjust height and width as needed
        videoId: videoID,
        playerVars: {
          enablejsapi: 1, // Enable JavaScript API,
        },
      });
	}
	else {

		const tag = document.createElement('script');
		tag.src = `https://www.youtube.com/iframe_api`; // YouTube iframe API script
		const firstScriptTag = document.getElementsByTagName('script')[0];
            if (firstScriptTag) {
                firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
            } else {
                // If no script tags are found, append to the head instead
                document.head.appendChild(tag);
            }


		window.onYouTubeIframeAPIReady = () => {
		player = new YT.Player('player', {
			height: '700',
			width: '100%', // Adjust height and width as needed
			videoId: videoID,
			playerVars: {
			enablejsapi: 1, // Enable JavaScript API,
			},
		});
		}

	}

	const pollingInterval = 100;
	intervalId = setInterval(getPlaybackPosition, pollingInterval);
	return () => clearInterval(intervalId);
  });

  onDestroy(() => {
		clearInterval(intervalId);
		if (player) player.destroy(); // Dispose of the player instance
	});



  function getPlaybackPosition() {
	if (player && player.getPlayerState() === YT.PlayerState.PLAYING) {
    const currentPosition = player.getCurrentTime();
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
	player.pauseVideo();
	console.log(event)
	// Set the span to editable on double click
	event.target.contentEditable = "true";
	// Optional: Focus the element automatically
	event.target.focus();

	// Add a listener for blur event to capture changes and reset editability
	event.target.addEventListener('blur', handleEditComplete);
	}

async function handleEditComplete(event) {
	player.seekTo(parseFloat(event.target.dataset.startSec))
	player.playVideo();
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

</script>

<h1>English Transcript for Video {videoID}</h1>

<div class="video-container">
	<div id="player"></div>
</div>


<div class="transcript-box">
	{#if transcript}
        <ul>
            {#each transcript as line (line.startSec)}
			<li data-start-sec={line.startSec}> 
				<div class="startTime-box">{line.startTime}</div> 
				<span contentEditable="false" on:dblclick={handleDoubleClick} data-docID={line.docID} data-start-sec={line.startSec}> {line.text} </span>
			</li>
            {/each}
        </ul>
	{/if}
</div>



<style>
    .startTime-box {
        box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.15); /* Adjust shadow as needed */
        padding: 5px; /* Optional padding for spacing */
        border-radius: 5px; /* Optional rounded corners */
        margin-right: 10px; /* Optional spacing between startTime and text */
		display: inline-block; /* Allow content to shrink to its width */
    }
    .transcript-box {
        width: 60%;         /* Make width half the page */
        height: 700px;      /* Adjust height as needed */
        overflow-y: scroll; /* Enable vertical scrolling */
        border: 1px solid #ccc; /* Optional border */
        float: right;       /* Align to the right */ 
    }
	.video-container {
		float: left; /* Float the video container to the left */
		width: 35%; /* Adjust width as needed */
	}
</style>

