# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
from firebase_functions import firestore_fn, https_fn, options, storage_fn, pubsub_fn

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore, storage
import boto3
import os
from pytube import YouTube
import googleapiclient.discovery
import requests
import time
from datetime import datetime
from datetime import timedelta
import deepl
import json
from google.cloud import videointelligence
from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.services.transcoder_service import (
    TranscoderServiceClient,
)

app = initialize_app()
db = firestore.client()

deeplTrans = deepl.Translator(os.environ['DEEPLKEY'])

project_id = "revolutiontranslate"
region = "us-central1"


@storage_fn.on_object_finalized()
def transcriptKickOff(event: storage_fn.CloudEvent[storage_fn.StorageObjectData]):
    bucket_name = event.data.bucket
    file_name = event.data.name
    file_uri = f"gs://{bucket_name}/{file_name}"
    file = file_name.split(r"/")[-1].split(".")[0]

    content_type = event.data.content_type

    if not file_name.startswith("videos/"):
        print(f"File not in 'videos' folder. Ignoring.")
        return

    if not content_type or not content_type.startswith("video/"):
        print(f"This is not a video. ({content_type})")
        return

    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]

    config = videointelligence.SpeechTranscriptionConfig(
        language_code="en-US", 
        enable_automatic_punctuation=True
    )
    video_context = videointelligence.VideoContext(speech_transcription_config=config)

    operation = video_client.annotate_video(
        request={
            "features": features,
            "input_uri": file_uri,
            "video_context": video_context,
            "output_uri": f"gs://{bucket_name}/transcriptComplete/{file}.json"
        }
    )

    print("\nProcessing video for speech transcription.")

    transcode_client = TranscoderServiceClient()

    parent = f"projects/{project_id}/locations/{region}"
    job = transcoder_v1.types.Job()
    job.input_uri = file_uri
    job.output_uri = f"gs://{bucket_name}/transcoded/{file}/"

    response = transcode_client.create_job(parent=parent, job=job)
    print(f"Transcode job started: {response.name}")




@storage_fn.on_object_finalized()
def transcriptProcess(event: storage_fn.CloudEvent[storage_fn.StorageObjectData]) -> None:
    bucket_name = event.data.bucket
    file_name = event.data.name
    file_uri = f"gs://{bucket_name}/{file_name}"
    file = file_name.split(r"/")[-1].split(".")[0]
    videoLink = f"gs://{bucket_name}/transcoded/{file}/sd.mp4"

    content_type = event.data.content_type

    if not file_name.startswith("transcriptComplete/"):
        print(f"File not in 'transcriptComplete' folder. Ignoring.")
        return

    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(file_name)
    data = blob.download_as_string()
    result = json.loads(data)

    videoName = result['annotation_results'][0]['input_uri'].split(r"/")[-1]

    print("Starting transcript process for "+videoName)

    root_doc_ref = db.collection("messageVideos").document()

    genTime = datetime.now()

    root_doc_ref.set({
            'videoName':videoName,
             'publishTime':genTime,
             'videoLink': videoLink
    })

    videoID = root_doc_ref.id

    batch = db.batch()

    dataDict = {'SRTID':0,
                'startTime':'',
                'endTime':'',
                'genTime':genTime,
                'startSec':'',
                'endSec':'',
                'text':'',
                'genUser':'Google Video Intellegence Annotate',
                'currentEdit':True}
    
    theseWords = []

    SRTID = 0
    for x in result['annotation_results'][0]['speech_transcriptions']:
        thisText = ""
        startTime = None
        thisIter = x['alternatives'][0].get('words')
        if thisIter is None:
            continue
        for index, word in enumerate(thisIter):
            theseWords.append({
                'wordStartSec':word['start_time'].get('seconds',0)+word['start_time'].get('nanos',0)*1e-9,
                'wordEndSec':word['end_time'].get('seconds',0)+word['end_time'].get('nanos',0)*1e-9,
                'word':word['word']
            })

            if thisText == "":
                startTime = word['start_time']

            punctCheck = any(char in word['word'] for char in [".",',','!','?'])

            if index == len(thisIter) - 1 and not punctCheck:
                word['word'] += "."
                punctCheck = True
            
            thisText += word['word']+" "

            if punctCheck:
                endTime = word['end_time']

                dataDict['SRTID'] = SRTID
                dataDict['startSec'] = startTime.get('seconds',0) + startTime.get('nanos',0)*1e-9
                dataDict['endSec'] = endTime.get('seconds',0) + endTime.get('nanos',0)*1e-9
                dataDict['startTime'] = _seconds_to_formatted_time(dataDict['startSec'])
                dataDict['endTime'] = _seconds_to_formatted_time(dataDict['endSec'])
                dataDict['text'] = thisText

                doc_ref = db.collection("messageVideos").document(videoID).collection("englishTranscript").document()
                batch.set(doc_ref,dataDict.copy())
                for k in theseWords:
                    words_ref = root_doc_ref.collection("words").document()
                    batch.set(words_ref,k)

                thisText = ""
                SRTID += 1
                theseWords = []
    batch.commit()
    print(f"{videoName} processing complete.")


def _seconds_to_formatted_time(total_seconds: float) -> str:
    # Calculate hours, minutes, and seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format the time
    formatted_time = "{:02d}:{:02d}:{:02d},{:03d}".format(int(hours), int(minutes), int(seconds), int((seconds - int(seconds)) * 1000))

    return formatted_time

# @https_fn.on_call(
#     cors=options.CorsOptions(
#         cors_origins="http://localhost:5173",  # Adjust to your specific origins
#         cors_methods=["POST"],  # Specify allowed methods
#     )
# )
@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins=[
            "http://localhost:5173",  # Add your specific origins here
            r"https://revolutiontranslate\.web\.app",
            r"revolutiontranslate\.web\.app$"
        ],
        cors_methods=["POST"],  # Specify allowed methods
    )
)
def deepLTranslate(req: https_fn.Request) -> https_fn.Response:
    # Check if the request method is POST
    if req.method != "POST":
        return https_fn.Response("Method not allowed", status=405)

    # Parse the JSON data from the request body
    try:
        data = json.loads(req.data)
        data = data['data']
        videoID = data['videoID']
    except Exception as e:
        return https_fn.Response(f"Error parsing JSON: {str(e)}", status=400)
    
    returnData = _getTranscript(videoID)
    englishData = returnData['englishTranscript']

    deepLEnglish = ""
    for item in englishData:
        deepLEnglish += item['text']+'<b> </b>'
    translationResult = deeplTrans.translate_text(deepLEnglish,source_lang='EN',target_lang='ES',split_sentences='nonewlines',tag_handling='html',formality='less')

    splitTranslate = translationResult.text.split('<b> </b>')
    del splitTranslate[-1]

    batch = db.batch()

    dataDict = {'SRTID':0,
                'startTime':'',
                'endTime':'',
                'genTime':'',
                'text':'',
                'genUser':'',
                'currentEdit':True}
    
    dataReturn = []
    
    for i,line in enumerate(englishData):

        dataDict['SRTID'] = line['SRTID']
        dataDict['startTime'] = line['startTime']
        dataDict['endTime'] = line['endTime']
        dataDict['text'] = splitTranslate[i]
        dataDict['genTime'] = datetime.now()
        dataDict['genUser'] = 'DeepLTranslate'
        dataDict['parentEnglish'] = line['docID']
        dataDict['startSec'] = line['startSec']
        dataDict['endSec'] = line['endSec']

        doc_ref = db.collection("messageVideos").document(videoID).collection("spanishTranscript").document()
        batch.set(doc_ref,dataDict.copy())

        dataDict['genTime'] = dataDict['genTime'].isoformat()
        
        dataReturn.append(dataDict.copy())

    batch.commit()

    completeData = _getTranscript(videoID)

    response = json.dumps({"data":completeData['spanishTranscript']})
    # Return a response
    return https_fn.Response(response, status=200)


@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins=[
            "http://localhost:5173",  # Add your specific origins here
            r"https://revolutiontranslate\.web\.app",
            r"revolutiontranslate\.web\.app$"
        ],
        cors_methods=["POST"],  # Specify allowed methods
    )
)
def getTranscript(req: https_fn.Request) -> https_fn.Response:

    # Check if the request method is POST
    if req.method != "POST":
        return https_fn.Response("Method not allowed", status=405)

    # Parse the JSON data from the request body
    try:
        data = json.loads(req.data)
        data = data['data']
        videoID = data['videoID']
    except Exception as e:
        return https_fn.Response(f"Error parsing JSON: {str(e)}", status=400)
    
    returnData = _getTranscript(videoID)

    returnResponse = json.dumps({"data":returnData})
    # Return a response
    return https_fn.Response(returnResponse, status=200)

def _getTranscript(videoID):
    returnData = {}

    doc_ref = db.collection("messageVideos").document(videoID)
    collections = doc_ref.collections()

    collection_names = [collection.id for collection in collections]

    for name in collection_names:
        if name == 'words':
            continue
        transcript_ref = db.collection("messageVideos").document(videoID).collection(name)
        transcript_query = transcript_ref.where("currentEdit", "==", True).order_by("startSec")
        transcript_fire = transcript_query.get()
        results = []
        for res in transcript_fire:
            thisRes = res.to_dict()
            thisRes['docID'] = res.id
            thisRes['genTime'] = thisRes['genTime'].isoformat()
            results.append(thisRes)

        returnData[name] = results.copy()

    return returnData
    

def stampToSec(stamp):
    components = stamp.split(",")

    hours = int(components[0].split(":")[0])
    minutes = int(components[0].split(":")[1])
    seconds = float(components[0].split(":")[2])
    milliseconds = int(components[1])

    totalSeconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return totalSeconds