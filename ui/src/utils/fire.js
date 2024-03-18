// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import {getStorage, getDownloadURL, ref, uploadBytesResumable } from "firebase/storage"
import { getFunctions, httpsCallable } from 'firebase/functions';
import { getFirestore, collection, getDocs, getDoc,setDoc, addDoc, doc, orderBy, query, where } from "firebase/firestore"
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
const getTranscriptFunc = httpsCallable(functions, 'getTranscript');

let currentUploadTask = null;

export class transcriptClass {
  constructor(videoID){
    this.videoID = videoID
    this.englishTranscript
    this.spanishTranscript
    this.videoURL = undefined
  }

  async init () {
    this.refreshTranscript()

    // console.log(this.englishTranscript)
    // console.log(this.spanishTranscript)
    const docRef = doc(db, 'messageVideos', this.videoID)
    const videoDoc = await getDoc(docRef)
    const videoData = videoDoc.data()

    this.videoURL = await getDownloadURL(ref(storage, videoData.videoLink))

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
  }

  async spanishTranslate() {
    const result = await deepLTranslate({ videoID: this.videoID })
    this.spanishTranscript = result.data
    spanishTranscript.set(result.data)

}
}

export async function getVideos() {
    const videoInfo = new Map();
    const fireVideo = await getDocs(collection(db, "messageVideos"));
  
    // Create a Promise to handle asynchronous operations
    const promise = new Promise((resolve) => {
      fireVideo.forEach((doc) => {
        console.log(`${doc.id} => ${doc.data()}`);

        const thisData = doc.data()

        thisData.jsTS = thisData.publishTime

        videoInfo.set(doc.id, thisData);
        // Resolve the promise after all iterations are done
        if (fireVideo.size === videoInfo.size) { // Check if all documents are processed
              // Convert map entries to an array and sort
              const sortedEntries = [...videoInfo.entries()].sort((a, b) => b[1].jsTS - a[1].jsTS);

            // Create a new map from the sorted entries
            const sortedVideoInfo = new Map(sortedEntries);
            resolve(sortedVideoInfo);
        }
      });
    });
  
    // Wait for the promise to resolve and return the videoInfo map
    return await promise;
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
      return {"docID":querySnapshot.docs[0].id,"positionScale":0}
    }


    if (currentDocData.text === event.target.textContent) {
      console.log("No Changes")
      return {"docID":docID,"positionScale":0}
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

    currentDocData.currentEdit = true
    currentDocData.parentDoc = docID
    currentDocData.genUser = 'Firebase App'
    currentDocData.genTime = new Date()
    currentDocData.text = event.target.textContent


    const newDocRef = collection(db, 'messageVideos', videoID, langSource)
    const newDocID = await addDoc(newDocRef,currentDocData)

    await setDoc(docRef, { currentEdit: false }, {merge: true})

    return {"docID":newDocID.id,"positionScale":positionScale}

}


export async function uploadVideo(file, onProgress) {

  const storageRef = ref(storage, `videos/${file.name}`);

  try {
    currentUploadTask = uploadBytesResumable(storageRef, file);

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