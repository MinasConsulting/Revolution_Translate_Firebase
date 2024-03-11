<script>
    import { getVideos, uploadVideo } from '../utils/fire.js';
    import { onMount } from 'svelte';


    let videoInfoPromise = getVideos()
    let selectedFile = null;
    let uploadProgress = 0;

    onMount(() => {
        let authenticated = localStorage.getItem('authenticated')
        if (!authenticated) {
            // // Redirect the user to the login page if not authenticated
            // authenticated = localStorage.getItem('authenticated') === 'true';
            window.location.href = '/login';
        }
    });

    const handleFileChange = (event) => {
        selectedFile = event.target.files[0];
    };


    const handleUpload = async () => {
        if (selectedFile) {
            const updateProgress = (progress) => {
            uploadProgress = progress;
            };

            try {
                await uploadVideo(selectedFile, updateProgress);
                console.log('File uploaded successfully!');
                // Handle successful upload and utilize the downloadURL if needed
            } catch (error) {
                console.error('Upload failed:', error);
                // Handle upload error (e.g., display an error message)
            }
        }
        };

</script>

{#await videoInfoPromise then videoInfo}

    <h1>Welcome to Revolution Translate</h1>

    <input type="file" accept="*" on:change={handleFileChange}>
    <button on:click={handleUpload}>Upload</button>

    {#if uploadProgress > 0}
    <p>Uploading... {uploadProgress}%</p>
    {/if}
    
        {#each [...videoInfo] as [videoID, value] (videoID)}
        <div class="parent-container">
            <div class="video-list">
            <li>
                <h2>{value.videoName}</h2>
            </li>
            <li>
                <a href={`/englishTranscript/${videoID}`} videoID={videoID} on:click={() => {localStorage.setItem('videoName', value.videoName);}}>
                    <img src="/Black Mark.png" alt="Message Thumbnail"/>
                </a>
            </li>
            </div>
        </div>
        {/each}
    
        <footer>
            Evan Stoelzel | Minas Consulting | evan@minas.consulting
        </footer>
    
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
    .video-list img {
    width: 250px;
    height: 250px;
}

</style>
