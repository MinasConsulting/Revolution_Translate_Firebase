# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
from firebase_functions import firestore_fn, https_fn
from firebase_functions import scheduler_fn

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore
import google.cloud.firestore
import boto3
import os
from pytube import YouTube
import googleapiclient.discovery
import requests
import time
from datetime import datetime
from datetime import timedelta


app = initialize_app()
db = firestore.client()


@scheduler_fn.on_schedule(schedule="every wednesday 22:00",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
def wedTranscriptGen(context) -> None:
    _transcriptGen(context)

@scheduler_fn.on_schedule(schedule="every saturday 20:00",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
def satTranscriptGen(context) -> None:
    _transcriptGen(context)

# @scheduler_fn.on_schedule(schedule="every sunday 23:00",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
@scheduler_fn.on_schedule(schedule="every monday 8:19",timezone=scheduler_fn.Timezone("America/Denver"),timeout_sec=540,memory=1024)
def sunTranscriptGen(context) -> None:
    _transcriptGen(context)




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