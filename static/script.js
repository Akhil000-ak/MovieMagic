// Movie data map (use same IDs as in home.html)
const movies = {
    "1": {
        title: "Kubeera",
        image: "/images/kubera.jpg",
        genre: "Action, Drama, Thriller",
        duration: "150 min",
        rating: "8.5/10",
        synopsis: "A gripping tale of power and redemption."
    },
    "2": {
        title: "Kannappa",
        image: "/images/kannappa.jpg",
        genre: "Action, Drama, Fantasy",
        duration: "160 min",
        rating: "8.1/10",
        synopsis: "An epic story of devotion and adventure."
    },
    "3": {
        title: "Sitaare Zameen Par",
        image: "/images/sitare.jpg",
        genre: "Comedy, Drama, Sports",
        duration: "140 min",
        rating: "7.9/10",
        synopsis: "Inspiring journey of underdogs in sports."
    },
    "4": {
        title: "Final Destination: Bloodlines",
        image: "/images/final destination.jpg",
        genre: "Horror, Supernatural, Thriller",
        duration: "120 min",
        rating: "7.2/10",
        synopsis: "Death comes for those who escape their fate."
    },
    "5": {
        title: "Bairavam",
        image: "/images/Bairavam.jpg",
        genre: "Action, Drama",
        duration: "145 min",
        rating: "7.8/10",
        synopsis: "A story of justice and vengeance."
    },
    "6": {
        title: "Thug-Life",
        image: "/images/thug-life.jpg",
        genre: "Action, Crime, Thriller",
        duration: "135 min",
        rating: "8.0/10",
        synopsis: "The rise and fall of a street legend."
    }
};

// Helper to get URL param
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

document.addEventListener('DOMContentLoaded', function() {
    // Dynamic Movie Details for booking.html
    const movieIdField = document.getElementById('movie-id');
    if (movieIdField) {
        const movieId = getQueryParam("movie");
        if (movieId && movies[movieId]) {
            // Set hidden input value for backend
            movieIdField.value = movieId;
            // Update movie details section
            document.getElementById('movie-title').textContent = movies[movieId].title;
            document.getElementById('movie-image').src = movies[movieId].image;
            document.getElementById('movie-image').alt = movies[movieId].title;
            document.getElementById('movie-genre').textContent = movies[movieId].genre;
            document.getElementById('movie-duration').textContent = movies[movieId].duration;
            document.getElementById('movie-rating').textContent = movies[movieId].rating;
            document.getElementById('movie-synopsis').textContent = movies[movieId].synopsis;
        } else {
            // No valid movie ID
            document.querySelector('.booking-container').innerHTML =
                "<p>Invalid or missing movie selection. Please return to the <a href='index.html'>home page</a>.</p>";
            return;
        }
    }

    // Navigation based on login status (now checks with backend)
    checkLoginStatus();

    // Logout functionality
    const logoutBtn = document.getElementById('logout-link');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            try {
                const response = await fetch('/logout', {
                    method: 'GET',
                    credentials: 'same-origin'
                });
                if (response.ok) {
                    window.location.href = '/';
                }
            } catch (error) {
                console.error('Logout failed:', error);
            }
        });
    }

    // Registration form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;

            if (password !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }

            const formData = {
                username: document.getElementById('username').value,
                password: password,
                email: document.getElementById('email').value
            };

            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();
                if (response.ok) {
                    window.location.href = '/login';
                } else {
                    alert(data.message || 'Registration failed');
                }
            } catch (error) {
                console.error('Registration error:', error);
                alert('Registration failed');
            }
        });
    }

    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = {
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData),
                    credentials: 'same-origin'
                });

                const data = await response.json();
                if (response.ok) {
                    window.location.href = '/home';
                } else {
                    alert(data.message || 'Login failed');
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('Login failed');
            }
        });
    }

    // Seat selection logic
    const seatMap = document.querySelector('.seat-map');
    const seatPrice = 10; // Set your price per seat here
    if (seatMap) {
        seatMap.addEventListener('click', function(e) {
            if (e.target.classList.contains('seat') && !e.target.classList.contains('occupied')) {
                e.target.classList.toggle('selected');
                updateSelectedCountAndPrice();
            }
        });
    }

    function updateSelectedCountAndPrice() {
        const selectedSeats = document.querySelectorAll('.seat.selected');
        document.getElementById('selected-seats-count').textContent = selectedSeats.length;
        document.getElementById('total-price').textContent = selectedSeats.length * seatPrice;
    }

    // Booking form submission
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const selectedSeats = document.querySelectorAll('.seat.selected');
            if (selectedSeats.length === 0) {
                alert('Please select at least one seat!');
                return;
            }
            const movieIdElem = document.getElementById('movie-id');
            const bookingData = {
                movie_id: movieIdElem ? movieIdElem.value : null,
                showtime: document.getElementById('booking-time').value,
                seats: Array.from(selectedSeats).map(seat => seat.textContent)
            };

            try {
                const response = await fetch('/booking', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(bookingData),
                    credentials: 'same-origin'
                });

                if (response.ok) {
                    window.location.href = '/tickets';
                } else {
                    alert('Booking failed');
                }
            } catch (error) {
                console.error('Booking error:', error);
                alert('Booking failed');
            }
        });
    }
});

async function checkLoginStatus() {
    try {
        const response = await fetch('/check-auth', {credentials: 'same-origin'});
        const data = await response.json();

        const loginLink = document.getElementById('login-link');
        const registerLink = document.getElementById('register-link');
        const logoutLink = document.getElementById('logout-link');

        if (data.authenticated) {
            if (loginLink) loginLink.style.display = 'none';
            if (registerLink) registerLink.style.display = 'none';
            if (logoutLink) logoutLink.style.display = 'block';
        } else {
            if (loginLink) loginLink.style.display = '';
            if (registerLink) registerLink.style.display = '';
            if (logoutLink) logoutLink.style.display = 'none';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}