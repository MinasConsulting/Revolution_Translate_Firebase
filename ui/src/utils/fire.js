// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import {getStorage, getDownloadURL, ref } from "firebase/storage"
import { getFunctions, httpsCallable } from 'firebase/functions';
import { getFirestore, collection, getDocs, getDoc,setDoc, addDoc, doc, orderBy, query, where } from "firebase/firestore"
// import { Translator } from 'deepl-node';
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional


import firebaseConfig from '../.secrets/firebaseSecret.json'
import otherSecrets from '../.secrets/otherSecrets.json'

// Initialize Firebase
const app = initializeApp(firebaseConfig);

const db = getFirestore(app)
const storage = getStorage(app)

const functions = getFunctions(app);
const deepLTranslate = httpsCallable(functions, 'deepLTranslate');
const getTranscriptFunc = httpsCallable(functions, 'getTranscript');

export class transcriptClass {
  constructor(videoID){
    this.videoID = videoID
    this.englishTranscript
    this.spanishTranscript
    this.videoURL
  }

  async init () {
    const transResult = await getTranscriptFunc({ videoID: this.videoID })
    if ('englishTranscript' in transResult.data){
      this.englishTranscript = transResult.data.englishTranscript
    }

    if ('spanishTranscript' in transResult.data){
      this.spanishTranscript = transResult.data.spanishTranscript
    }

    // console.log(this.englishTranscript)
    // console.log(this.spanishTranscript)

    this.videoURL = await getDownloadURL(ref(storage, "gs://revolutiontranslate.appspot.com/videos/Copy of Sunday_3_3_Resi_1234565434.mp4"))
    console.log(this.videoURL)

  }

  async spanishTranslate() {
    const result = await deepLTranslate({ videoID: this.videoID })
    console.log(result)  

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

        // Parse the timestamp string into milliseconds since epoch (1970-01-01T00:00:00Z)
        const timestampInMilliseconds = Date.parse(thisData.publishTime);

        // Create a new Date object from the milliseconds
        const dateObject = new Date(timestampInMilliseconds);

        thisData.jsTS = dateObject

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

export async function getTranscript(videoID) {
    const transcript = [];
    const englishTranscriptRef = query(
        collection(db, "messageVideos", videoID, "englishTranscript"),
        where("currentEdit", "==",true),
        orderBy("SRTID") // Order by the field 'SRTID'
    );

    // Get the documents and construct a promise that resolves when all values are pushed
    return new Promise((resolve, reject) => {
        getDocs(englishTranscriptRef)
        .then((snapshot) => {
            snapshot.forEach((doc) => {
            const data = doc.data();
        
            data.startSec = stampToSec(data.startTime)
            data.endSec = stampToSec(data.endTime)
            data.docID = doc.id
            transcript.push(data);
            });
            // Resolve with the complete transcript array
            resolve(transcript);
        })
        .catch((error) => {
            reject(error); // Reject with the error if any
        });
    });
}

export async function saveChange(event,videoID) {

    const docID = event.target.dataset.docid
    const docRef = doc(db, 'messageVideos', videoID, 'englishTranscript', docID)
    const currentDoc = await getDoc(docRef)
    const currentDocData = currentDoc.data()

    if (currentDocData.text === event.target.textContent) {
      console.log("No Changes")
      return docID
    }

    currentDocData.currentEdit = true
    currentDocData.parentDoc = docID
    currentDocData.genUser = 'Firebase App'
    currentDocData.genTime = new Date()
    currentDocData.text = event.target.textContent


    const newDocRef = collection(db, 'messageVideos', videoID, 'englishTranscript')
    const newDocID = await addDoc(newDocRef,currentDocData)

    await setDoc(docRef, { currentEdit: false }, {merge: true})

    return newDocID.id

}

export async function getTranslation(videoID) {
  const result = await deepLTranslate({"englishText":"My name is Evan"})
  console.log(result)

}

async function deepLExecute(deepLEnglish) {
  const apiKey = otherSecrets.deepL
  const apiUrl = 'https://api.deepl.com/v2/translate';

  const requestData = {
      auth_key: apiKey,
      text: deepLEnglish,
      source_lang: 'EN',
      target_lang: 'ES',
      split_sentences: 'nonewlines',
      tag_handling: 'html',
      formality: 'less'
  };

  try {
      const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
      });

      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }

      const responseData = await response.json();
      return responseData.translations[0].text;
  } catch (error) {
      console.error('Error:', error);
      // Handle error appropriately
      return null;
  }
}


function stampToSec(stamp) {
    const components = stamp.split(",")

    const hours = parseInt(components[0].split(":")[0]);
    const minutes = parseInt(components[0].split(":")[1]);
    const seconds = parseFloat(components[0].split(":")[2]);
    const milliseconds = parseInt(components[1]);

    // Convert to seconds and return the result
    const totalSeconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
    return totalSeconds
}


