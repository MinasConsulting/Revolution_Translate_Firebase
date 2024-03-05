# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
from firebase_functions import firestore_fn, https_fn, options, storage_fn, pubsub_fn

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore, storage
import google.cloud.firestore
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
import pathlib

app = initialize_app()
db = firestore.client()

deeplTrans = deepl.Translator(os.environ['DEEPLKEY'])


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


@storage_fn.on_object_finalized()
def transcriptProcess(event: storage_fn.CloudEvent[storage_fn.StorageObjectData]) -> None:
    bucket_name = event.data.bucket
    file_name = event.data.name
    file_uri = f"gs://{bucket_name}/{file_name}"
    file = file_name.split(r"/")[-1].split(".")[0]

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
             'videoLink': "gs:/"+result['annotation_results'][0]['input_uri']
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


    SRTID = 0
    for x in result['annotation_results'][0]['speech_transcriptions']:
        thisText = ""
        startTime = None
        thisIter = x['alternatives'][0].get('words')
        if thisIter is None:
            continue
        for index, word in enumerate(thisIter):
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
                dataDict['startSec'] = startTime['seconds'] + startTime.get('nanos',0)*1e-9
                dataDict['endSec'] = endTime['seconds'] + endTime.get('nanos',0)*1e-9
                dataDict['startTime'] = _seconds_to_formatted_time(dataDict['startSec'])
                dataDict['endTime'] = _seconds_to_formatted_time(dataDict['endSec'])
                dataDict['text'] = thisText

                doc_ref = db.collection("messageVideos").document(videoID).collection("englishTranscript").document()
                batch.set(doc_ref,dataDict.copy())

                thisText = ""
                SRTID += 1
    print(f"{videoName} processing complete.")
    batch.commit()


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
        cors_origins="http://localhost:5173",  # Adjust to your specific origins
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

        doc_ref = db.collection("messageVideos").document(videoID).collection("spanishTranscript").document()
        batch.set(doc_ref,dataDict.copy())

        dataDict['genTime'] = dataDict['genTime'].isoformat()
        
        dataReturn.append(dataDict.copy())

    batch.commit()

    response = json.dumps({"data":dataReturn})
    # Return a response
    return https_fn.Response(response, status=200)


@https_fn.on_request(
            cors=options.CorsOptions(
        cors_origins="http://localhost:5173",  # Adjust to your specific origins
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
        transcript_ref = db.collection("messageVideos").document(videoID).collection(name)
        transcript_query = transcript_ref.where("currentEdit", "==", True).order_by("SRTID")
        transcript_fire = transcript_query.get()
        results = []
        for res in transcript_fire:
            thisRes = res.to_dict()
            thisRes['docID'] = res.id
            thisRes['genTime'] = thisRes['genTime'].isoformat()
            thisRes['startSec'] = stampToSec(thisRes['startTime'])
            thisRes['endSec'] = stampToSec(thisRes['endTime'])
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
# @scheduler_fn.on_schedule(schedule="every wednesday 22:00",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
# def wedTranscriptGen(context) -> None:
#     _transcriptGen(context)

# @scheduler_fn.on_schedule(schedule="every saturday 20:00",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
# def satTranscriptGen(context) -> None:
#     _transcriptGen(context)

# # @scheduler_fn.on_schedule(schedule="every sunday 23:00",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
# @scheduler_fn.on_schedule(schedule="every monday 8:19",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
# def sunTranscriptGen(context) -> None:
#     _transcriptGen(context)


# @https_fn.on_request(
#             cors=options.CorsOptions(
#         cors_origins="http://localhost:5173",  # Adjust to your specific origins
#         cors_methods=["POST"],  # Specify allowed methods
#     )
# )
# def awsScript(req: https_fn.Request) -> https_fn.Response:

#     videoID = '-mNT1N8ZgWE'

#     api_service_name = "youtube"
#     api_version = "v3"
#     DEVELOPER_KEY = os.environ['YOUTUBEKEY']

#     # API client
#     youtube = googleapiclient.discovery.build(
#             api_service_name, api_version, developerKey = DEVELOPER_KEY)

#     print("Executing Video Overried with id "+ videoID)
#     request = youtube.videos().list(
#         part="snippet",
#         id=videoID,
#     )

#     response = request.execute()

#     publishedTime = response['items'][0]['snippet']['publishedAt']
#     title = response['items'][0]['snippet']['title']

#     jobName = videoID+"-"+str(int(time.time()))
#     # jobName = '0gbhuya2-XU-1708218034'
#     print(f"Transcribe Job Name: {jobName}")

#     doc_ref = db.collection("messageVideos").document(videoID)

#     doc_snapshot = doc_ref.get()

# # Check if the document exists
#     if doc_snapshot.exists:
#         return https_fn.Response(json.dumps({"data":"Exists"}), status=200)


#     doc_ref.set({
        
#             'videoName':title,
             
#              'publishTime':publishedTime,
#              'videoType':'livestream',
#             #  'videoLength':5700,
#             #  'generatedItag':151,
#              'maxSRTID':maxSrid
#             #  'messageStartSRTID':169,
#             # 'messageEndSRTID':1064})
#     })

#     transcribeClient = boto3.client('transcribe',
#                                     aws_access_key_id=os.environ['AWSKEY'],
#                                     aws_secret_access_key=os.environ['AWSSECRET'],
#                                     region_name='us-west-2')


#     response = transcribeClient.start_transcription_job(TranscriptionJobName=jobName,
#                                                         Media={'MediaFileUri':f's3://revolution-church-transcribe/AudioUploads/{videoID}.mp3'},
#                                                         LanguageCode = 'en-US',
#                                                         Subtitles={'Formats':['srt']})
    
#     # response = transcribeClient.get_transcription_job(
#     #     TranscriptionJobName='-mNT1N8ZgWE-1709513712'
#     # )
    
#     status = "IN_PROGRESS"
#     while status not in ["COMPLETED", "FAILED"]:
#         response = transcribeClient.get_transcription_job(TranscriptionJobName=jobName)
#         status = response["TranscriptionJob"]["TranscriptionJobStatus"]
#         print(f"Job status: {status}")
#         time.sleep(5)  # Adjust sleep time as needed
    
#     downloadLink = response['TranscriptionJob']['Subtitles']['SubtitleFileUris'][0]
#     requestsGet = requests.get(downloadLink)
#     rawSRT = requestsGet.text

#     srtLines = rawSRT.split('\n')

#     maxSrid = int(srtLines[-3])

#     print(maxSrid)

#     batch = db.batch()

#     counter = 0
#     dataDict = {'SRTID':0,
#                 'startTime':'',
#                 'endTime':'',
#                 'genTime':'',
#                 'text':'',
#                 'genUser':'',
#                 'currentEdit':True}
    
#     for line in srtLines:
#         if counter == 0:
#             SRTID = int(line.strip())
#             dataDict['SRTID'] = SRTID
#             counter += 1
            
#         elif counter == 1:
#             timeSplit = line.split(' --> ')
#             dataDict['startTime'] = timeSplit[0].strip()
#             dataDict['endTime'] = timeSplit[1].strip()
#             counter += 1
            
#         elif counter == 2:
#             dataDict['text'] = line.strip()
#             counter += 1
            
#         elif counter == 3:
#             dataDict['genTime'] = datetime.now()
#             dataDict['genUser'] = 'AWS Transcribe'
#             counter = 0

#             doc_ref = db.collection("messageVideos").document(videoID).collection("englishTranscript").document()
#             batch.set(doc_ref,dataDict.copy())

#     batch.commit()

#     return https_fn.Response(json.dumps({"data":"done"}), status=200)
    


def _transcriptGen(context) -> None:

    if os.environ.get('FUNCTIONS_EMULATOR', False) == 'true':
        print("change emulator directory")
        os.chdir('/tmp')
    else:
        os.mkdir('/tmp')
        os.chdir('/tmp')

    print("function started")
    s3Client = boto3.client('s3',
                            aws_access_key_id=os.environ['AWSKEY'],
                            aws_secret_access_key=os.environ['AWSSECRET'])

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = os.environ['YOUTUBEKEY']

    # API client
    youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey = DEVELOPER_KEY)

    if 'VIDEOIDOVERRIDE' not in os.environ:
        request = youtube.search().list(
            part="snippet",
            channelId=os.environ['CHURCHCHANID'],
            type='video',
            eventType='completed',
            order='date',
            maxResults=1
        )

        response = request.execute()
        videoID = response['items'][0]['id']['videoId']

    else:
        print("Executing Video Overried with id "+ os.environ['VIDEOIDOVERRIDE'])
        request = youtube.videos().list(
            part="snippet",
            id=os.environ['VIDEOIDOVERRIDE'],
        )

        response = request.execute()
        videoID=os.environ['VIDEOIDOVERRIDE']

    publishedTime = response['items'][0]['snippet']['publishedAt']
    title = response['items'][0]['snippet']['title']
    fileName = videoID+'.webm'
    # fileName = videoID+'.mp4'

    print(response)
    yt = YouTube('http://youtube.com/watch?v='+videoID)

    print(yt.streams.filter(only_audio=True))

    audioStream = yt.streams.get_by_itag(251)
    # audioStream = yt.streams.get_by_itag(140)

    if audioStream is None:
        print("ITAG 251 not found. Reschedule for in 30m in future")
        next_execution_time = db.collection('__function_schedule__').document(context.function_name).get().get('nextExecutionTime') + timedelta(minutes=30)
        db.collection('__function_schedule__').document(context.function_name).update({'nextExecutionTime': next_execution_time})
        return


    print(os.listdir())

    audioStream.download(filename=fileName)

    print(os.listdir())

    s3Client.upload_file(Filename='./'+fileName,
            Bucket=os.environ['CHURCHTRANSCRIBEBUCKET'],
            Key='AudioUploads/' + fileName)

    transcribeClient = boto3.client('transcribe',
                                    aws_access_key_id=os.environ['AWSKEY'],
                                    aws_secret_access_key=os.environ['AWSSECRET'],
                                    region_name='us-west-2')

    jobName = videoID+"-"+str(int(time.time()))
    # jobName = '0gbhuya2-XU-1708218034'
    print(f"Transcribe Job Name: {jobName}")

    response = transcribeClient.start_transcription_job(TranscriptionJobName=jobName,
                                                        Media={'MediaFileUri':'s3://revolution-church-transcribe/AudioUploads/'+fileName},
                                                        LanguageCode = 'en-US',
                                                        Subtitles={'Formats':['srt']})
    
    status = "IN_PROGRESS"
    while status not in ["COMPLETED", "FAILED"]:
        response = transcribeClient.get_transcription_job(TranscriptionJobName=jobName)
        status = response["TranscriptionJob"]["TranscriptionJobStatus"]
        print(f"Job status: {status}")
        time.sleep(5)  # Adjust sleep time as needed
    
    downloadLink = response['TranscriptionJob']['Subtitles']['SubtitleFileUris'][0]
    requestsGet = requests.get(downloadLink)
    rawSRT = requestsGet.text

    srtLines = rawSRT.split('\n')

    maxSrid = int(srtLines[-3])

    print(maxSrid)

    # replace with videoID
    # videoID = '0gbhuya2-XU'
    doc_ref = db.collection("messageVideos").document(videoID)

    doc_ref.set({
        
            'videoName':title,
             
             'publishTime':publishedTime,
             'videoType':'livestream',
            #  'videoLength':5700,
            #  'generatedItag':151,
             'maxSRTID':maxSrid
            #  'messageStartSRTID':169,
            # 'messageEndSRTID':1064})
    })

    batch = db.batch()

    counter = 0
    dataDict = {'SRTID':0,
                'startTime':'',
                'endTime':'',
                'genTime':'',
                'text':'',
                'genUser':'',
                'currentEdit':True}
    
    for line in srtLines:
        if counter == 0:
            SRTID = int(line.strip())
            dataDict['SRTID'] = SRTID
            counter += 1
            
        elif counter == 1:
            timeSplit = line.split(' --> ')
            dataDict['startTime'] = timeSplit[0].strip()
            dataDict['endTime'] = timeSplit[1].strip()
            counter += 1
            
        elif counter == 2:
            dataDict['text'] = line.strip()
            counter += 1
            
        elif counter == 3:
            dataDict['genTime'] = datetime.now()
            dataDict['genUser'] = 'AWS Transcribe'
            counter = 0

            doc_ref = db.collection("messageVideos").document(videoID).collection("englishTranscript").document()
            batch.set(doc_ref,dataDict.copy())

    batch.commit()