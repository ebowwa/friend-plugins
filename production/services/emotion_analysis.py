# services/emotion_analysis.py
import os
from hume import HumeBatchClient
from hume.models.config import ProsodyConfig

async def analyze_emotion(filename: str) -> str:
    try:
        client = HumeBatchClient(os.environ["HUME_API_KEY"])
        prosody_config = ProsodyConfig()
        job = await client.submit_job(None, [prosody_config], files=[filename])

        print("Running...", job)
        await job.await_complete()
        print("Job completed with status: ", job.get_status())

        emotion_scores = {}
        emotion_counts = {}
        full_predictions = job.get_predictions()
        for source in full_predictions:
            predictions = source["results"]["predictions"]
            for prediction in predictions:
                prosody_predictions = prediction["models"]["prosody"]["grouped_predictions"]
                for prosody_prediction in prosody_predictions:
                    for segment in prosody_prediction["predictions"]:
                        for emotion in segment["emotions"]:
                            if emotion["name"] in emotion_scores:
                                emotion_scores[emotion["name"]] += emotion["score"]
                                emotion_counts[emotion["name"]] += 1
                            else:
                                emotion_scores[emotion["name"]] = emotion["score"]
                                emotion_counts[emotion["name"]] = 1
        
        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        message = "Your speech was "
        emotion_messages = []
        for i in range(3):
            emotion = sorted_emotions[i][0]
            score = int(sorted_emotions[i][1] * 100 / emotion_counts[emotion])
            emotion_messages.append(f"{emotion} {score}%")
        message += ", ".join(emotion_messages)
        return message
    except Exception as e:
        raise Exception(f"Error in emotion analysis: {str(e)}")