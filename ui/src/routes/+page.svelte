<script>
    import { getVideos } from '../utils/fire.js';

    let videoInfoPromise = getVideos()

</script>

{#await videoInfoPromise then videoInfo}

    <h1>Welcome to Revolution Translate</h1>
    
        {#each [...videoInfo] as [videoID, value] (videoID)}
        <div class="parent-container">
            <div class="video-list">
            <li>
                {value.videoName}
            </li>
            <li>
                <a href={`/englishTranscript/${videoID}`} videoID={videoID}>
                    <img src="https://i.ytimg.com/vi/{videoID}/hqdefault.jpg" alt="Message Thumbnail"/>
                </a>
            </li>
            </div>
        </div>
        {/each}
    
{:catch error}
	<p style="color: red">{error.message}</p>
{/await}

<style>

    :golbal(body), :global(html) {
        background-color: black;
        color: white;
    }
    .parent-container {
        display: list-item;
        justify-content: center;
        align-items: center;
        height:50vh;
        flex-direction: column;
        /* border: 2px solid #751c1c;
        padding: 5px;
        border-radius: 2px; */
    }

    .video-list{
        list-style: none;
        padding: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }

</style>

