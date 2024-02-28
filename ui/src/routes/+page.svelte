<script>
    import { getVideos } from '../utils/fire.js';

    let videoInfoPromise = getVideos()

</script>

{#await videoInfoPromise then videoInfo}

    <h1>Welcome to SvelteKit</h1>
    
        {#each [...videoInfo] as [videoID, value] (videoID)}
            <li>
                <img src="https://i.ytimg.com/vi/{videoID}/mqdefault.jpg" alt="Message Thumbnail"/>
                {value.videoName}
                <a href={`/englishTranscript/${videoID}`} videoID={videoID}>English Transcript</a>
            </li>
        {/each}
    
{:catch error}
	<p style="color: red">{error.message}</p>
{/await}

