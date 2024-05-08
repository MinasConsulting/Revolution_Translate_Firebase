<script>
    import { getVideos, uploadVideo, cancelUpload } from '../utils/fire.js';
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
      } catch (error) {
        console.error('Upload failed:', error);
        // Handle upload error (e.g., display an error message)
      }
    }
  };

  const handleCancel = () => {
    uploadProgress = -1
    cancelUpload()
  }

</script>

{#await videoInfoPromise then videoInfo}

<div class="header-container">
    <img src="/Revolution Church - Full Horiztonal Black SM.png" style="max-width:22%; height:auto">
    <div class="upload-container">
        <input type="file" accept="video/*" on:change={handleFileChange}>
        <button on:click={handleUpload}>Upload</button>
        {#if uploadProgress > 0 && uploadProgress < 100}
            <button on:click={handleCancel}>Cancel Upload</button>
            <p>Uploading... {uploadProgress}%</p>
        {:else if uploadProgress == 100}
            <p>Upload complete.<br>
                Video will be available in 15-30 minutes.</p>
        {:else if uploadProgress == -1}
            <p>Upload cancelled.</p>
        {/if}
    </div>
</div>
    
{#each [...videoInfo] as [videoID, value] (videoID)}
    <div class="video-list">
    <li>
    <div class="video-list-item">
        <p style="width: 22%;"><b>{value.videoName}</b></p>
        <div class="edit-button-container">
            <a 
              class = "edit-button"
              href={`/englishTranscript/${videoID}`} 
              videoID={videoID} 
              on:click={() => {localStorage.setItem('videoName', value.videoName);}}>
                Edit
            </a>
          </div>
          <p style="width: 10%;"><u>Length:</u> {value.vidLength.endTime.slice(0,-4)}</p>
        <p style="width: 20%;"><u>Generated Time:</u> {value.publishTime.toDate().toLocaleDateString("default", {year: "numeric"})}/{value.publishTime.toDate().toLocaleDateString("default", {month: "2-digit"})}/{value.publishTime.toDate().toLocaleDateString("default", {day: "2-digit"})} {value.publishTime.toDate().toLocaleTimeString()}</p>
        <p style="width: 20%;"><u>Last English Edit:</u> {value.englishMessageData.genTime.toDate().toLocaleDateString("default", {year: "numeric"})}/{value.englishMessageData.genTime.toDate().toLocaleDateString("default", {month: "2-digit"})}/{value.englishMessageData.genTime.toDate().toLocaleDateString("default", {day: "2-digit"})} {value.englishMessageData.genTime.toDate().toLocaleTimeString()}</p>
        {#if value.spanishMessageData}
            <p style="width: 20%;"><u>Last Spanish Edit:</u> {value.spanishMessageData.genTime.toDate().toLocaleDateString("default", {year: "numeric"})}/{value.spanishMessageData.genTime.toDate().toLocaleDateString("default", {month: "2-digit"})}/{value.spanishMessageData.genTime.toDate().toLocaleDateString("default", {day: "2-digit"})} {value.spanishMessageData.genTime.toDate().toLocaleTimeString()}</p>
        {:else}
            <p style="width: 20%;"><u>Last Spanish Edit:</u> NA</p>
        {/if}
    </div>
    </li>
    </div>
{/each}

<footer class="footer">
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
    .video-list{
        list-style: none;
        padding: 0;
        display: flex;
        flex-direction: column;
        align-items: left;
    }
.header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 2px solid white;
        padding: 10px;
    }

    .upload-container {
        display: flex;
        flex-direction: column; /* Render items vertically */
        gap: 5px;
        border: 1px solid black; /* Add border to upload container */
        padding: 10px; /* Optional: Add padding for better appearance */
    }
    .video-list-item {
    display: flex;
    justify-content: left;
    align-items: center; /* Maintain vertical alignment in center */
    line-height: 15px; /* Adjust line spacing for text */
    border: 1px solid black;
    white-space: normal;
  word-wrap: break-word; /* Allow breaking words */
}
.edit-button {
    color: white;
    background-color: black;
    padding: 5px;
    text-decoration: none;
}
.edit-button-container {
  padding: 5px; /* Adjust padding as needed */
  padding-right: 3%;
}

.footer {
  position: fixed; /* Fix the footer to its position */
  bottom: 0; /* Anchor it to the bottom of the viewport */
  width: 100%; /* Set width to 100% to span the entire width */
}

</style>
