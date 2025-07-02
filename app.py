import os
from flask import Flask, render_template, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from boto3.dynamodb.conditions import Key
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

# AWS Services Configuration
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns_client = boto3.client('sns', region_name='us-east-1')

# Initialize DynamoDB Tables
users_table = dynamodb.Table('MovieUsers')
movies_table = dynamodb.Table('Movies')
bookings_table = dynamodb.Table('Bookings')

# SNS Topic ARN (Create this in AWS Console first)
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN') 

# Sample movies data
sample_movies = {
    1: {"title": "Kubeera", "genre": "Action", "showtimes": ["10:00", "14:00", "18:00"]},
    2: {"title": "Kannappa", "genre": "Drama", "showtimes": ["11:00", "15:00", "19:00"]},
    3: {"title": "Final Destination", "genre": "Sci-Fi", "showtimes": ["12:00", "16:00", "20:00"]}
}

def publish_sns_notification(email, message):
    """Publish notification to SNS topic"""
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='Movie Booking Confirmation',
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': email
                }
            }
        )
        return response
    except Exception as e:
        print(f"Error sending SNS notification: {e}")
        return None

@app.route('/booking', methods=['POST'])
def make_booking():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    movie_id = int(data['movie_id'])
    movie = sample_movies.get(movie_id)
    
    if not movie:
        return jsonify({'success': False, 'message': 'Movie not found'}), 404
    
    showtime = data['showtime']
    if showtime not in movie['showtimes']:
        return jsonify({'success': False, 'message': 'Invalid showtime'}), 400
    
    seats = int(data['seats'])
    if seats <= 0:
        return jsonify({'success': False, 'message': 'Invalid number of seats'}), 400
    
    # Get user email from DynamoDB
    user_response = users_table.get_item(Key={'username': session['username']})
    user_email = user_response['Item']['email']
    
    booking_id = str(uuid.uuid4())
    
    # Create booking record
    bookings_table.put_item(
        Item={
            'booking_id': booking_id,
            'username': session['username'],
            'movie_id': movie_id,
            'movie_title': movie['title'],
            'showtime': showtime,
            'seats': seats,
            'status': 'confirmed'
        }
    )
    
    # Prepare and send SNS notification
    message = f"""
    Booking Confirmed!
    Movie: {movie['title']}
    Showtime: {showtime}
    Seats: {seats}
    Booking ID: {booking_id}
    """
    
    sns_response = publish_sns_notification(user_email, message)
    
    if not sns_response:
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'message': 'Booking confirmed but notification failed'
        })
    
    return jsonify({
        'success': True,
        'booking_id': booking_id,
        'message': 'Booking confirmed. Notification sent.'
    })

# ... [rest of your existing routes remain the same] ...