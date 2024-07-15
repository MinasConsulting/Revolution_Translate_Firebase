// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import {getStorage, getDownloadURL, ref, uploadBytesResumable, getBlob } from "firebase/storage"
import { getFunctions, httpsCallable } from 'firebase/functions';
import { getFirestore, collection, getDocs, getDoc, updateDoc, doc, orderBy, query, where, limit } from "firebase/firestore"
import { englishTranscript, spanishTranscript } from './stores.js';
// import { Translator } from 'deepl-node';
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional


import firebaseConfig from '../.secrets/firebaseSecret.json'

// Initialize Firebase
const app = initializeApp(firebaseConfig);

const db = getFirestore(app)
const storage = getStorage(app)

const functions = getFunctions(app);
const deepLTranslate = httpsCallable(functions, 'deepLTranslate');
const gptTranslate = httpsCallable(functions, 'gptTranslate',{timeout: 300000});
const getTranscriptFunc = httpsCallable(functions, 'getTranscript');
const saveChangeCall = httpsCallable(functions, 'saveChange')

let currentUploadTask = null;

export class transcriptClass {
  constructor(videoID){
    this.videoID = videoID
    this.englishTranscript
    this.spanishTranscript
    this.videoURL = undefined
  }

  async init () {
    await this.refreshTranscript()

    // console.log(this.englishTranscript)
    // console.log(this.spanishTranscript)
    const docRef = doc(db, 'messageVideos', this.videoID)
    const videoDoc = await getDoc(docRef)
    const videoData = videoDoc.data()


    this.videoURL = await getDownloadURL(ref(storage, videoData.videoLink))

  }

  // async downloadVideoBLOB(videoName) {
  //   console.log(`videos/${videoName}`)
  //   const storageRef = ref(storage, `videos/${videoName}`)
  
  //   try {
  //     // Get the blob from the Firebase storage reference
  //     const blob = await getBlob(storageRef);
  
  //     // Create a link element, use it to download the Blob, and remove it
  //     const link = document.createElement('a');
  //     link.href = URL.createObjectURL(blob);
  //     link.download = videoName;
  //     document.body.appendChild(link);
  //     link.click();
  //     document.body.removeChild(link);
  //     URL.revokeObjectURL(link.href);
  //     console.log("File downloaded successfully");
  //     return true;
  //   } catch (error) {
  //     console.error("Error downloading file:", error);
  //     return false;
  //   }
  // }

  async downloadVideo(videoName) {
    console.log(`videos/${videoName}`);
    const storageRef = ref(storage, `videos/${videoName}`);
  
    try {
      // Get the download URL from the Firebase storage reference
      const downloadURL = await getDownloadURL(storageRef);
  
      // Create a link element, set the href to the download URL, and trigger the download
      const link = document.createElement('a');
      link.href = downloadURL;
      link.download = videoName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      console.log("File downloaded successfully");
      return true;
    } catch (error) {
      console.error("Error downloading file:", error);
      return false;
    }
  }
  
  
  
  
  

  async refreshTranscript () {
    const transResult = await getTranscriptFunc({ videoID: this.videoID })
    if ('englishTranscript' in transResult.data){
      this.englishTranscript = transResult.data.englishTranscript
      englishTranscript.set(this.englishTranscript)
    }

    if ('spanishTranscript' in transResult.data){
      this.spanishTranscript = transResult.data.spanishTranscript
      spanishTranscript.set(this.spanishTranscript)
    }

    // Detect sync Issues
    // console.log("English Length",this.englishTranscript.length)
    // console.log("Spanish Length",this.spanishTranscript.length)

    // for (let i = 0; i < this.englishTranscript.length; i++){
    //   if (this.englishTranscript[i].docID !== this.spanishTranscript[i].parentEnglish) {
    //     console.log("Out of sync")
    //     console.log(this.englishTranscript[i])
    //     console.log(this.spanishTranscript[i])
    //     break
    //   }
    // }

    // Find last edited line
    // let genTime = this.englishTranscript[0].genTime
    // let maxIndex = 0
    // for (let i = 0; i < this.englishTranscript.length; i++){
    //   if (this.englishTranscript[i].genTime > genTime){
    //     maxIndex = i
    //     genTime = this.englishTranscript[i].genTime
    //   }

    //   }
    //   console.log(this.englishTranscript[maxIndex])

    
    }
  

  async spanishTranslate() {
    // const result = await deepLTranslate({ videoID: this.videoID })
    const result = await gptTranslate({ videoID: this.videoID })
    this.spanishTranscript = result.data
    spanishTranscript.set(result.data)

}
}

export async function getVideos() {
  const videoInfo = new Map();
  const fireVideo = await getDocs(collection(db, "messageVideos"));

  // Process each video asynchronously using Promise.all
  await Promise.all(
    fireVideo.docs.map(async (doc) => {

      const thisData = doc.data();

      const thisMessageRef = collection(db, "messageVideos", doc.id, 'englishTranscript');
      const messageQuery = query(thisMessageRef, orderBy("genTime", "desc"), limit(1));

      // Await the getDocs call for the message transcript
      const messageSnapshot = await getDocs(messageQuery);
      if (messageSnapshot.docs.length>0) {
        const messageData = messageSnapshot.docs[0].data();
        thisData.englishMessageData = messageData;
      } // Access data of the first document

      const spanishthisMessageRef = collection(db, "messageVideos", doc.id, 'spanishTranscript');
      const spanishmessageQuery = query(spanishthisMessageRef, orderBy("genTime", "desc"), limit(1));

      // Await the getDocs call for the message transcript
      const spanishmessageSnapshot = await getDocs(spanishmessageQuery);
      if (spanishmessageSnapshot.docs.length>0) {
        const spanishmessageData = spanishmessageSnapshot.docs[0].data(); // Access data of the first document
        thisData.spanishMessageData = spanishmessageData;
      }

      const messageLenRef = collection(db, "messageVideos", doc.id, 'englishTranscript');
      const messageLenRefQuery = query(messageLenRef, orderBy("endSec", "desc"), limit(1));

      // Await the getDocs call for the message transcript
      const messageLenRefSnapshot = await getDocs(messageLenRefQuery);
      if (messageLenRefSnapshot.docs.length>0) {
        const messageLenData = messageLenRefSnapshot.docs[0].data(); // Access data of the first document
        thisData.vidLength = messageLenData;
      }


      thisData.jsTS = thisData.publishTime;

      videoInfo.set(doc.id, thisData);
      // console.log(`${doc.id}`, thisData);
    })
  );

  // Sort the videoInfo map after all async operations are complete
  const sortedEntries = [...videoInfo.entries()].sort((a, b) => b[1].jsTS - a[1].jsTS);
  const sortedVideoInfo = new Map(sortedEntries);

  return sortedVideoInfo;
}

export async function saveRead(transcriptLine,videoID,langSource) {
    const docID = transcriptLine.docID
    const docRef = doc(db, 'messageVideos', videoID, langSource, docID)
    await updateDoc(docRef, {lineRead: true})
}

export async function saveChange(event,videoID) {

    const docID = event.target.dataset.docid
    const langSource = event.target.dataset.language
    const docRef = doc(db, 'messageVideos', videoID, langSource, docID)
    const currentDoc = await getDoc(docRef)
    const currentDocData = currentDoc.data()

    const parentRef = collection(db, 'messageVideos', videoID, langSource)
    const parentQuery = query(parentRef, where("parentDoc","==",docID))
    const querySnapshot = await getDocs(parentQuery) 

    if (querySnapshot.docs.length > 0) {
      const thisDocData = querySnapshot.docs[0].data()
      console.log("New edit not saving")
      alert("Newer edit detected and loaded. Please re edit")
      event.target.textContent = thisDocData.text
      return {"docID":querySnapshot.docs[0].id,"positionScale":0,'refresh':true}
    }


    if (currentDocData.text === event.target.textContent) {
      console.log("No Changes")
      return {"docID":docID,"positionScale":0,'refresh':false}
    }

    const currentTextArray = currentDocData.text.split(" ")
    const newTextArray = event.target.textContent.split(" ")
    let positionScale = 0

    for (var i = 0; i < newTextArray.length; i++){
      if (currentTextArray[i] !== newTextArray[i]){
        positionScale = i/newTextArray.length
        break
      }
    }

    try {
        await saveChangeCall({ "videoID": videoID, 
                            "langSource": langSource,
                            "originDocID": docID,
                            "newText": event.target.textContent})
     
      return { positionScale: positionScale, refresh: true };

    } catch (error) {

        if(langSource === "englishTranscript") {
          englishTranscript.update(transcript => transcript.filter(line => line.docID !== docID));
        }
        else if (langSource === "spanishTranscript") {
          spanishTranscript.update(transcript => transcript.filter(line => line.docID !== docID));
        }

        console.error("Error saving change:", error);
        alert("Failed to save changes. Please try again.");

        return { positionScale: 0, refresh: true }; // Or any other appropriate response
    }

}



export async function uploadVideo(file, onProgress) {
  const metadata = {
    contentDisposition: `attachment; filename="${file.name}"`
  };

  const storageRef = ref(storage, `videos/${file.name}`);

  try {
    // Include the metadata in the upload
    currentUploadTask = uploadBytesResumable(storageRef, file, metadata);

    currentUploadTask.on(
      "state_changed",
      (snapshot) => {
        // Provide progress updates to the onProgress callback function
        const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        onProgress(progress.toFixed(2));
      },
      (error) => {
        console.error("Upload failed:", error);
        throw error; // Re-throw the error for handling in the Svelte component
      }
    );

    // Alternatively, you can await the completion without onProgress:
    // await uploadTask;
  } catch (error) {
    console.error("Upload failed:", error);
    throw error; // Re-throw the error for handling in the Svelte component
  }
}

export function cancelUpload() {
  if (currentUploadTask) {
    currentUploadTask.cancel();
    currentUploadTask = null;
    console.log("Upload canceled");
  }
}