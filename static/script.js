// Correct modal and button references
const modal = document.getElementById("favorites-popup"); // Use the correct modal ID
const addButton = document.getElementById("add-favorite-btn"); // Button that opens the modal
const closeButton = document.getElementById("close-popup"); // Close button inside the modal
const favoritesList = document.getElementById("favorites-list"); // Favorites list table body (ensure this ID exists)

// Open modal
addButton.addEventListener("click", () => {
    modal.style.display = "flex"; // Show the modal when the button is clicked
});

// Close modal
closeButton.addEventListener("click", () => {
    modal.style.display = "none"; // Hide the modal when the close button is clicked
});

// Close modal when clicking outside the modal content
window.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.style.display = "none"; // Hide the modal if the background is clicked
    }
});

// Form submission for adding favorites
document.getElementById('add-favorite-form').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent default form submission

    const formData = new FormData(this);

    fetch('/add_favorite', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (response.ok) {
                // Fetch the new favorite details from the form data
                const routeName = formData.get('route');
                const stopName = formData.get('stop');

                // Dynamically update the favorites list in the UI
                const newRow = document.createElement("tr");
                newRow.innerHTML = `
                    <td>${stopName}</td>
                    <td>${routeName}</td>
                    <td>Active</td> <!-- Example status, update as needed -->
                `;
                favoritesList.appendChild(newRow);

                modal.style.display = "none"; // Close the modal
                this.reset(); // Reset the form
            } else {
                alert('Failed to add favorite stop. Please try again.');
            }
        })
        .catch(error => console.error('Error adding favorite:', error));
});

document.getElementById("route-select").addEventListener("change", function() {
    const routeName = this.value;
    const stopSelect = document.getElementById("stop-select");

    // Clear previous stops
    stopSelect.innerHTML = '<option value="">Select Stop</option>';

    if (routeName) {
        fetch(`/get_stops_by_route?route=${routeName}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(stop => {
                    const option = document.createElement("option");
                    option.value = stop.id;
                    option.textContent = stop.name;
                    stopSelect.appendChild(option);
                });
            })
            .catch(error => console.error('Error fetching stops:', error));
    }
});

// Populate modal with example stops (if necessary)
document.addEventListener("DOMContentLoaded", () => {
    const modalStopList = document.getElementById("modal-stop-list");
    const stops = ['Park Street', 'Boylston', 'Copley', 'Arlington']; // Example stops

    stops.forEach((stop) => {
        const stopButton = document.createElement("li");
        stopButton.innerHTML = `<button onclick="addFavorite('${stop}')">${stop}</button>`;
        modalStopList.appendChild(stopButton);
    });
});
