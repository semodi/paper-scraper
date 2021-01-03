from recommend import get_recommendations
import json

def handler(event, context):
    if 'body' in event:
        data = json.loads(event['body'])
    else:
        data = event
    user_id = data.get('user_id', 0)
    cutoff_days = data.get('cutoff_days', 20)
    no_papers = data.get('no_papers', 10)
    results = get_recommendations(user_id, cutoff_days, no_papers).to_dict('records')
    results.append(event)
    return results
