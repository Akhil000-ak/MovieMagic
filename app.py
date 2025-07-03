from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from botocore.exceptions import ClientError
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

# AWS Services setup
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
DYNAMODB_USERS = os.environ.get('DYNAMODB_USERS', 'MovieAppUsers')
DYNAMODB_BOOKINGS = os.environ.get('DYNAMODB_BOOKINGS', 'MovieAppBookings')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:324037304857:Moviemagic:06001d83-4d79-449c-b031-5e0e4d978688')

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
users_table = dynamodb.Table(DYNAMODB_USERS)
bookings_table = dynamodb.Table(DYNAMODB_BOOKINGS)
sns_client = boto3.client('sns', region_name=AWS_REGION)

movies = {
    1: {"title": "Kubeera", "genre": "Action", "showtimes": ["10:00", "14:00", "18:00"]},
    2: {"title": "Kannappa", "genre": "Drama", "showtimes": ["11:00", "15:00", "19:00"]},
    3: {"title": "Final Destination", "genre": "Sci-Fi", "showtimes": ["12:00", "16:00", "20:00"]}
}

def send_booking_confirmation(username, movie_title, showtime, seats):
    """Send booking confirmation via SNS"""
    try:
        # Get user's email from DynamoDB
        user_data = users_table.get_item(Key={'username': username})
        email = user_data['Item'].get('email', '')
        
        if not email:
            print("No email found for user, cannot send notification")
            return False
            
        message = f"""
        Booking Confirmation for {username}:
        
        Movie: {movie_title}
        Showtime: {showtime}
        Seats: {seats}
        
        Thank you for your booking!
        """
        
        # Publish to SNS topic
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=f"Booking Confirmation: {movie_title}",
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': email
                }
            }
        )
        
        print(f"Notification sent to {email}, MessageId: {response['MessageId']}")
        return True
        
    except ClientError as e:
        print(f"Error sending SNS notification: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check-auth')
def check_auth():
    return jsonify({'authenticated': 'username' in session})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password = data['password']
        email = data['email']
        try:
            resp = users_table.get_item(Key={'username': username})
            if 'Item' in resp:
                return jsonify({'success': False, 'message': 'Username already exists'}), 400
            users_table.put_item(Item={
                'username': username,
                'password': generate_password_hash(password),
                'email': email
            })
            return jsonify({'success': True})
        except ClientError as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password = data['password']
        try:
            resp = users_table.get_item(Key={'username': username})
            user = resp.get('Item')
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
        except ClientError as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    return render_template('home.html', movies=movies)

@app.route('/booking/<int:movie_id>')
def booking_page(movie_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    movie = movies.get(movie_id)
    if not movie:
        flash('Movie not found', 'error')
        return redirect(url_for('home'))
    return render_template('booking.html', movie=movie)

@app.route('/booking', methods=['POST'])
def make_booking():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    movie_id = int(data['movie_id'])
    movie = movies.get(movie_id)
    if not movie:
        return jsonify({'success': False, 'message': 'Movie not found'}), 404
    showtime = data['showtime']
    if showtime not in movie['showtimes']:
        return jsonify({'success': False, 'message': 'Invalid showtime'}), 400
    seats = data['seats']
    if not isinstance(seats, int) or seats <= 0:
        return jsonify({'success': False, 'message': 'Invalid number of seats'}), 400
    
    booking_data = {
        'username': session['username'],
        'movie_id': str(movie_id),
        'movie_title': movie['title'],
        'showtime': showtime,
        'seats': seats
    }
    
    try:
        # Store booking in DynamoDB
        bookings_table.put_item(Item=booking_data)
        
        # Send SNS notification
        send_booking_confirmation(
            username=session['username'],
            movie_title=movie['title'],
            showtime=showtime,
            seats=seats
        )
        
        return jsonify({'success': True})
    except ClientError as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/tickets')
def tickets():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        resp = bookings_table.scan(
            FilterExpression='username = :username',
            ExpressionAttributeValues={':username': session['username']}
        )
        user_bookings = resp.get('Items', [])
    except Exception:
        user_bookings = []
    return render_template('tickets.html', bookings=user_bookings)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
